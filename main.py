import requests, json
import pandas as pd
from datetime import datetime
import streamlit as st
import streamlit_authenticator as stauth
import seaborn as sns
import matplotlib.pyplot as plt


st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")

url = 'https://script.google.com/macros/s/AKfycbwOFDUXCrRtMEQY4GXJ_jwp9x9Lp7NF3n06s9uU0NVF268iQo0jGvENvPBWHvWTalu4/exec'

list_data = []
with requests.Session() as session:
    for i, data in enumerate(requests.get(url).json()['status']):
        if i == 0:
            colunas = data
        else:
            list_data.append(data)

df = pd.DataFrame.from_records(list_data, columns=colunas)

classes_a_exibir = ['Troca', 'Abandono total', 'Abandono parcial', 'Upgrade', 'Lost piloto', 'Piloto parcial']

# (df['Quantidade Devolução - Calculado - Total'] != '(No value)') & (df['Ticket status'].isin(['Concluido', 'Devolução Cancelada'])) &
filtros = \
    (df['CO - Quantidade - Calculado - Total de dispositivos para devolução'] != '(No value)') & \
        (df['Pedido data - Daily'] != '(No value)') & (df['supply__devolucao__tipo'].isin(classes_a_exibir))

df = df[filtros]

lista = df.values.tolist()


dic_lista = {}
for i in lista:
    dealId = str(i[1])
    data_de_solicitacao = i[8]
    qtd_prevista = int(i[6])
    status_ticket = str(i[3])
    try:
        if status_ticket in ['Concluido', 'Devolução Cancelada']:
            qtd_feita = int(i[7])
        else:
            qtd_feita = 0
    except:
        qtd_feita = 0
    classe = i[9]
    
    try:
        data_realizacao = datetime.strptime(str(i[5]).split('T')[0], "%Y-%m-%d")
    except:
        data_realizacao = "-"
    if dealId not in dic_lista:
        dic_lista[dealId] = {
            'data_de_solicitacao' : data_de_solicitacao,
            'qtd_prevista' : qtd_prevista,
            'qtd_realizada' : qtd_feita,
            'data_conclusão' : data_realizacao,
            'classe' : classe
        }

    else:
        try:
            if dic_lista[dealId]['data_conclusão'] < data_realizacao:
                dic_lista[dealId]['data_conclusão'] = data_realizacao
        except:
            pass

        dic_lista[dealId]['qtd_realizada'] += qtd_feita


list_df = []
for i in dic_lista:
    data_de_solicitacao = datetime.strptime(str(dic_lista[i]['data_de_solicitacao']).split('T')[0], '%Y-%m-%d')
    semana_solicitacao = int(data_de_solicitacao.strftime("%U")) + 1
    data_conclusao = dic_lista[i]['data_conclusão']
    try:
        semana_conclusao = int(data_conclusao.strftime("%U")) + 1
        semanas_em_aberto = abs(int(semana_conclusao) - int(semana_solicitacao))
    except:
        pass
    # verifica Status
    if dic_lista[i]['qtd_prevista'] == dic_lista[i]['qtd_realizada']:
        status = 'Concluído'
    else:
        status = 'Pendente'
        
    
    list_df.append( [i, dic_lista[i]['data_de_solicitacao'], dic_lista[i]['qtd_prevista'], dic_lista[i]['qtd_realizada'],\
                    dic_lista[i]['data_conclusão'], dic_lista[i]['classe'], semana_solicitacao, semana_conclusao, semanas_em_aberto, status ] )
    

colunas = ['Deal Id', 'data_de_solicitacao', 'qtd_prevista', 'qtd_realizada', 'data_conclusão', 'classe', 'semana_solicitacao', 'semana_conclusao', 'semanas_em_aberto', 'status']

df = pd.DataFrame.from_records(list_df, columns=colunas)

# inicia contrução do coHort
maior_valor = (df['semana_solicitacao'].values.max() if df['semana_solicitacao'].values.max() >= df['semana_conclusao'].values.max() \
               else df['semana_conclusao'].values.max()) + 1

concluidos = df[(df.status == 'Concluído')]

coHort_concluidos = []
for cont, y in enumerate(range(1, maior_valor)):

    percentil_do_total_solicitado_disp = 0
    percentil_do_total_solicitado_deals = 0

    for x in range(0, maior_valor - cont):
        filtro_df =concluidos[(concluidos.semana_solicitacao == y) & (concluidos.semanas_em_aberto == x)]
        qtd_disp_concluidos = filtro_df['qtd_realizada'].sum()
        qtd_de_deals = filtro_df['semana_solicitacao'].count()

        if qtd_de_deals > 0:
            df_da_semana = df[(df.semana_solicitacao == y)]
            percentil_do_total_solicitado_disp = round( ( percentil_do_total_solicitado_disp + (qtd_disp_concluidos / df_da_semana['qtd_prevista'].sum()) * 100 ), 2) 
            percentil_do_total_solicitado_deals = round( (percentil_do_total_solicitado_deals + (qtd_de_deals / df_da_semana['semana_solicitacao'].count()) * 100 ), 2)

        coHort_concluidos.append([
            y, x, qtd_de_deals, percentil_do_total_solicitado_deals, qtd_disp_concluidos, percentil_do_total_solicitado_disp
        ])

colunas = ['Semana Deal', 'Semana em relação ao Deal', 'qtd_deal', 'acumulado', 'qtd_realizada', 'acumulado_disp']
coHort = pd.DataFrame.from_records(coHort_concluidos, columns=colunas)
coHort_cont_deals_concluidos = coHort.pivot_table(values='qtd_deal', index='Semana Deal', columns='Semana em relação ao Deal')
coHort_percent_deals_concluidos = coHort.pivot_table(values='acumulado', index='Semana Deal', columns='Semana em relação ao Deal')
coHort_sum_disp_concluidos = coHort.pivot_table(values='qtd_realizada', index='Semana Deal', columns='Semana em relação ao Deal')
coHort_percentual_disp_concluidos = coHort.pivot_table(values='acumulado_disp', index='Semana Deal', columns='Semana em relação ao Deal')
df.to_csv('test.csv')
class Funcoes_de_visualizacao():
    def filtrosStreamlit():
        st.html(f'<h1 style="color : #666666">Completude - Devolução</h1>')
        # Filtros
        st.sidebar.markdown("##### Propriedades de exibição")
        largura = st.sidebar.select_slider(
            "tamanho do eixo X em relação ao eixo Y",
            options=range(28, 100),
            value=(28))

        altura = st.sidebar.select_slider(
            "tamanho do eixo Y em relação ao eixo x",
            options=range(0, 100),
            value=(8))
    
        return [altura, largura]

    def criaCoHort(base, largura, altura, descricao_base):
        f, ax = plt.subplots(figsize=(largura, altura))
        cmap = ['#e67c73', '#f8d567', '#f1d469', '#f1d469', '#e2d26c', '#dad06e', '#d3cf6f', '#cbce71', '#c4cd72', '#bccc74', '#b5ca76',\
                '#aec977', '#a6c879', '#9fc77a', '#97c67c', '#90c47e', '#88c37f', '#81c281', '#79c182', '#72c084', '#6abe86']
        
        st.html('<hr>')
        st.html(f'<h3 style="color : #666666">Fechamento por {descricao_base}</h3>')
        monthly_sessions = sns.heatmap(base, 
                            annot=True,
                            annot_kws={"size": 10, "color" : "black"}, 
                            linewidths=0.5, 
                            ax=ax, 
                            cmap=cmap, 
                            square=False,
                            fmt='.3g'
                            )

        ax.set_xlabel("Semana em relação ao Deal",fontsize=12)
        ax.set_ylabel("Semanas de Abertura",fontsize=12)
        
        plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = False, labeltop=True)
        st.pyplot(plt.show())


response = Funcoes_de_visualizacao.filtrosStreamlit()
Funcoes_de_visualizacao.criaCoHort(base=coHort_cont_deals_concluidos, largura=response[1], altura=response[0], descricao_base='Deals Concluídos')
Funcoes_de_visualizacao.criaCoHort(base=coHort_percent_deals_concluidos, largura=response[1], altura=response[0], descricao_base="% Acumulado de Deals Concluídos")
Funcoes_de_visualizacao.criaCoHort(base=coHort_sum_disp_concluidos, largura=response[1], altura=response[0], descricao_base="Total de Dispositivos")
Funcoes_de_visualizacao.criaCoHort(base=coHort_percentual_disp_concluidos, largura=response[1], altura=response[0], descricao_base="% Acumulado de Dispositivos Concluídos")

