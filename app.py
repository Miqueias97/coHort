import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import requests, json
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")

headers = {
  'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxncXBjY2J0b2FmanlhZ2NhdmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTI3NTkxNzYsImV4cCI6MjAyODMzNTE3Nn0.8Eztx6ygiqK6jP48BC7TsXwevH0Ji-GbpRdMkOI-_m0'
}

#
response = requests.request("GET", 'https://lgqpccbtoafjyagcavbd.supabase.co/rest/v1/users', headers=headers).json()

config = {
    'credentials': {
        'usernames': {
        }
    }, 
    'cookie': {
        'expiry_days': 1, 
        'key': 'some_signature_key', 
        'name': 'some_cookie_name'
    }
}

for i in response:
    config['credentials']['usernames'][i['user']] = {
        'name' : str(i['nome']),
        'logged_in': False,
        'password': str(i['pass'])
    }


authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Bem Vindo *{st.session_state["name"]}*')

    
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
            for y in range(1, maior_valor):
                soma_semana = 0
                for x in range(0, eixoX - cont):
                        qtd = df[(df.semana_solicitacao == y) & (df.semanas_em_aberto == x)]
                        qtd = qtd['semana_solicitacao'].count()
                        if qtd > 0:
                            qtd_div = df[(df.semana_solicitacao == y)]
                            qtd_div = qtd_div['semana_solicitacao'].count()
                            soma_semana = soma_semana + (qtd / qtd_div)
                        new_coHort.append([y, x, qtd, round(float(soma_semana), 2)])
                
                cont +=1

            colunas = ['Semana Deal', 'Semana em relação ao Deal', 'qtd_deal', 'acumulado']

            newCohor = pd.DataFrame.from_records(new_coHort, columns=colunas)

            data = newCohor.pivot_table(values='qtd_deal', index='Semana Deal', columns='Semana em relação ao Deal')
            acumulado = newCohor.pivot_table(values='acumulado', index='Semana Deal', columns='Semana em relação ao Deal')
            return {
                'corHort_deal' : data,
                'acumulado' : acumulado
            }

    class Funcoes_de_visualizacao():
        def ViewStreamlit(new_coHort, label, acumulado):
            st.html(f"<h1>Completude - Devolução {label}</h1>")
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




            # Graficos
            f, ax = plt.subplots(figsize=(largura, altura))
            cmap = ['#e67c73', '#f8d567', '#f1d469', '#f1d469', '#e2d26c', '#dad06e', '#d3cf6f', '#cbce71', '#c4cd72', '#bccc74', '#b5ca76',\
                    '#aec977', '#a6c879', '#9fc77a', '#97c67c', '#90c47e', '#88c37f', '#81c281', '#79c182', '#72c084', '#6abe86']
            
            st.html('<hr>')
            st.html('<h3 style="color : #666666">Fechamento por Deal Id</h3>')
            monthly_sessions = sns.heatmap(new_coHort, 
                                annot=True,
                                annot_kws={"size": 10, "color" : "black"}, 
                                linewidths=0.5, 
                                ax=ax, 
                                cmap=cmap, #'Spectral', 
                                square=False
                                )

            ax.set_xlabel("Semana em relação ao Deal",fontsize=12)
            ax.set_ylabel("Semanas de Abertura",fontsize=12)
            
            plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = False, labeltop=True)
            st.pyplot(plt.show())

            # acumulado
            f, ax = plt.subplots(figsize=(largura, altura))
            cmap = ['#e67c73', '#f8d567', '#f1d469', '#f1d469', '#e2d26c', '#dad06e', '#d3cf6f', '#cbce71', '#c4cd72', '#bccc74', '#b5ca76',\
                    '#aec977', '#a6c879', '#9fc77a', '#97c67c', '#90c47e', '#88c37f', '#81c281', '#79c182', '#72c084', '#6abe86']
            
            st.html('<hr>')
            st.html('<h3 style="color : #666666">Fechamento por Deal Id Acumulado</h3>')
            monthly_sessions = sns.heatmap(acumulado, 
                                annot=True,
                                annot_kws={"size": 10, "color" : "black"}, 
                                linewidths=0.5, 
                                ax=ax, 
                                cmap=cmap, #'Spectral', 
                                square=False
                                )

            ax.set_xlabel("Semana em relação ao Deal",fontsize=12)
            ax.set_ylabel("Semanas de Abertura",fontsize=12)
            
            plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = False, labeltop=True)
            st.pyplot(plt.show())



        # Leitura do arquivo base

    url = 'https://script.google.com/macros/s/AKfycbwOFDUXCrRtMEQY4GXJ_jwp9x9Lp7NF3n06s9uU0NVF268iQo0jGvENvPBWHvWTalu4/exec'

    list_data = []
    with requests.Session() as session:
        for i, data in enumerate(requests.get(url).json()['status']):
            if i == 0:
                colunas = data
            else:
                list_data.append(data)


    df = pd.DataFrame.from_records(list_data, columns=colunas)

    #df = pd.read_excel(r'hubspot-custom-report-devolucoes-2024-06-05.xls')

    # Realiza filtragem do dataframe
    classes_a_exibir = ['Troca', 'Abandono total', 'Abandono parcial', 'Upgrade', 'Lost piloto', 'Piloto parcial']
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

    new_coHort = Funcoes_de_manipulacao.coHort(df)['corHort_deal']
    acumulado = Funcoes_de_manipulacao.coHort(df)['acumulado']

    Funcoes_de_visualizacao.ViewStreamlit(new_coHort, label, acumulado)
