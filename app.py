import pandas as pd
from datetime import datetime
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import requests, json
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")


class Funcoes_de_manipulacao():
    # constroi novo DataFrame
    def new_Dataframe(lista):
        dic_lista = {}
        for i in lista:
            dealId = str(i[1])
            data_de_solicitacao = i[8]
            qtd_prevista = int(i[6])
            qtd_feita = int(i[7])
            classe = i[9]
            try:
                data_realizacao = datetime.strptime(str(i[5]).split('T')[0], "%Y-%m-%d")
                if dealId not in dic_lista:
                    dic_lista[dealId] = {
                        'data_de_solicitacao' : data_de_solicitacao,
                        'qtd_prevista' : qtd_prevista,
                        'qtd_realizada' : qtd_feita,
                        'data_conclusão' : data_realizacao,
                        'classe' : classe
                    }

                else:
                    if dic_lista[dealId]['data_conclusão'] < data_realizacao:
                        dic_lista[dealId]['data_conclusão'] = data_realizacao
                    
                    dic_lista[dealId]['qtd_realizada'] += qtd_feita
            except:
                pass

        colunas = ['Deal Id', 'data_de_solicitacao', 'qtd_prevista', 'qtd_realizada', 'data_conclusão', 'classe', 'semana_solicitacao', 'semana_conclusao', 'semanas_em_aberto']
        list_df = []

        for i in dic_lista:
            if dic_lista[i]['qtd_prevista'] == dic_lista[i]['qtd_realizada']:
                # Verifica dia da semana de solicitação
                data_de_solicitacao = datetime.strptime(str(dic_lista[i]['data_de_solicitacao']).split('T')[0], '%Y-%m-%d')
                semana_solicitacao = int(data_de_solicitacao.strftime("%U")) + 1
                data_conclusao = dic_lista[i]['data_conclusão']
                semana_conclusao = int(data_conclusao.strftime("%U")) + 1
                semanas_em_aberto = abs(int(semana_conclusao) - int(semana_solicitacao))
                

                list_df.append( [i, dic_lista[i]['data_de_solicitacao'], dic_lista[i]['qtd_prevista'], dic_lista[i]['qtd_realizada'],\
                                dic_lista[i]['data_conclusão'], dic_lista[i]['classe'], semana_solicitacao, semana_conclusao, semanas_em_aberto ] )
                
        df = pd.DataFrame.from_records(list_df, columns=colunas)
        return df

    # cria estrutura tabelar para coHort    
    def coHort(df):
        maior_semana_criacao = df['semana_solicitacao'].values.max()
        maior_semana_conclusao = df['semana_conclusao'].values.max()
        maior_valor = max([maior_semana_conclusao, maior_semana_criacao])  + 1
        eixoX = maior_valor
        new_coHort = []
        cont = 0
        for y in range(0, maior_valor):
            for x in range(0, eixoX - cont):
                    qtd = df[(df.semana_solicitacao == y) & (df.semana_conclusao == x)]
                    qtd = qtd['semana_solicitacao'].count()
                    new_coHort.append([x, y, qtd])
            
            cont +=1

        colunas = ['Semana Deal', 'Semana em relação ao Deal', 'qtd_deal']

        newCohor = pd.DataFrame.from_records(new_coHort, columns=colunas)

        data = newCohor.pivot_table(values='qtd_deal', index='Semana Deal', columns='Semana em relação ao Deal')
        return data

class Funcoes_de_visualizacao():
    def ViewStreamlit(new_coHort, label):
        # Filtros
        st.sidebar.markdown("##### Propriedades de exibição")
        largura = st.sidebar.select_slider(
            "tamanho do eixo X em relação ao eixo Y",
            options=range(28, 100),
            value=(28))

        altura = st.sidebar.select_slider(
            "tamanho do eixo Y em relação ao eixo x",
            options=range(0, 100),
            value=(12))




        # Graficos
        f, ax = plt.subplots(figsize=(largura, altura))
        cmap = ['#e67c73', '#d5d06f', '#abc978', '#81c281', '#57bb8a']
        st.html(f"<h1>Completude - Devolução {label}</h1>")
        monthly_sessions = sns.heatmap(new_coHort, 
                            annot=True,
                            annot_kws={"size": 8, "color" : "black"}, 
                            linewidths=0.5, 
                            ax=ax, 
                            cmap=cmap, 
                            square=False
                            )

        ax.set_xlabel("Semana em relação ao Deal",fontsize=12)
        ax.set_ylabel("Semanas de Abertura",fontsize=12)
        
        plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = False, labeltop=True)
        st.pyplot(plt.show())



    # Leitura do arquivo base

url = 'https://script.google.com/macros/s/AKfycbwOFDUXCrRtMEQY4GXJ_jwp9x9Lp7NF3n06s9uU0NVF268iQo0jGvENvPBWHvWTalu4/exec'

list_data = []
for i, data in enumerate(requests.get(url).json()['status']):
    if i == 0:
        colunas = data
    else:
        list_data.append(data)


df = pd.DataFrame.from_records(list_data, columns=colunas)

#df = pd.read_excel(r'hubspot-custom-report-devolucoes-2024-06-05.xls')

# Realiza filtragem do dataframe
classes_a_exibir = ['Troca', 'Abandono parcial']
filtros = (df['Quantidade Devolução - Calculado - Total'] != '(No value)') & (df['Ticket status'].isin(['Concluido', 'Devolução Cancelada'])) &\
    (df['CO - Quantidade - Calculado - Total de dispositivos para devolução'] != '(No value)') & \
        (df['Pedido data - Daily'] != '(No value)') & (df['supply__devolucao__tipo'].isin(classes_a_exibir))
df = df[filtros]

# atribui valores do dataframe a uma lista
lista = df.values.tolist()


df = Funcoes_de_manipulacao.new_Dataframe(lista)

# Atribui Filtro de Classe no streamlit
classes = ["Todas as Classes"]
classes.extend(df['classe'].unique().tolist())
filtrar_classe = st.sidebar.selectbox("Filtrar por Classe do Pedido:", classes)
label = ''
if filtrar_classe != "Todas as Classes":
    df = df[(df['classe'] == filtrar_classe)]
    label = f'( {filtrar_classe} )'

new_coHort = Funcoes_de_manipulacao.coHort(df)






Funcoes_de_visualizacao.ViewStreamlit(new_coHort, label)
