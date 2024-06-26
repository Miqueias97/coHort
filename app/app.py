import requests, json, asyncio, os
import pandas as pd
from datetime import datetime
import streamlit as st
import streamlit_authenticator as stauth
import seaborn as sns
import matplotlib.pyplot as plt


class Estruturacao_dos_dados():
    # constroi df com base nos dados armazenados no sheets e filtra baseado nas classes de interesse
    def obtencao_dos_dados(classes_para_filtro, status_concluidos, pipeline):
        # obtem dados e agrupa os Deals
        if pipeline == 'Devolução':
            url = 'https://script.google.com/macros/s/AKfycbwOFDUXCrRtMEQY4GXJ_jwp9x9Lp7NF3n06s9uU0NVF268iQo0jGvENvPBWHvWTalu4/exec'
        else:
            url = 'https://script.google.com/macros/s/AKfycbwX0NDc1S7Ze4tyFla1kt0UkcZ3JhtepXSJ7KTcWBkeU-LxuZS2qn908nK6v76uZtpBSg/exec'
        deals = {}
        with requests.Session() as session:
            base_de_dados = session.get(url).json()['status']
            for i, data in enumerate(base_de_dados):
                if i > 0: # esta função é necessária pois a api retorna o cabeçalho da pagina 
                    # https://docs.google.com/spreadsheets/d/1Vdh6_eUNrQ59ij13kZoRESZJ0_ncc5su-fgmJchKiZ4/edit#gid=842775073
                    classe_do_pedido = data[9]
                    if classe_do_pedido in classes_para_filtro:
                        deal_id = data[1]
                        status = data[3]
                        data_abertura_do_deal = data[8]
                        # Calcula semana de abertura
                        try:
                            semana_de_abertura = datetime.strptime(str(data_abertura_do_deal).split('T')[0], '%Y-%m-%d')
                            semana_de_abertura = int(semana_de_abertura.strftime("%U")) + 1
                        except:
                            semana_de_abertura = None

                        try:
                            qtd_prevista = int(data[6])
                        except:
                            qtd_prevista = None
                        if status in status_concluidos and qtd_prevista != None:
                            closed_date = data[5]
                            try:
                                semana_de_conclusao = datetime.strptime(str(closed_date).split('T')[0], '%Y-%m-%d')
                                semana_de_conclusao = int(semana_de_conclusao.strftime("%U")) + 1
                            except:
                                semana_de_conclusao = None
                            try:
                                qtd_devolvida = int(data[7])
                            except:
                                qtd_devolvida = 0
                        else:
                            closed_date, qtd_devolvida, semana_de_conclusao = None, 0, None 
                        
                        # pre-defini variaveis 
                        semanas_em_aberto_deal = None
                        status_devolucao = 'Pendente'
                        if deal_id not in deals:

                            # Valida se a Devolucão foi concluida
                            if qtd_prevista == qtd_devolvida:
                                status_devolucao = 'Concluido'
                            
                            if semana_de_conclusao != None and semana_de_abertura != None:
                                semanas_em_aberto_deal = semana_de_conclusao - semana_de_abertura


                            deals[deal_id] = {
                            'data_abertura_do_deal' : data_abertura_do_deal,
                            'classe_do_pedido' : classe_do_pedido,
                            'closed_date' : closed_date,
                            'qtd_prevista' : qtd_prevista,
                            'qtd_devolvida' : qtd_devolvida,
                            'status_devolucao' : status_devolucao,
                            'semana_de_abertura' : semana_de_abertura,
                            'semana_de_conclusao' : semana_de_conclusao,
                            'semanas_em_aberto_deal' : semanas_em_aberto_deal
                        }
                        else:
                            if closed_date != None:
                                # substitui data anterior caso ela seja None
                                if deals[deal_id]['closed_date'] == None:
                                    deals[deal_id]['closed_date'] = closed_date
                                    try:
                                        semana_de_conclusao = datetime.strptime(str(deals[deal_id]['closed_date']).split('T')[0], '%Y-%m-%d')
                                        semana_de_conclusao = int(semana_de_conclusao.strftime("%U")) + 1
                                    except:
                                        semana_de_conclusao = None
                                    deals[deal_id]['semana_de_conclusao'] = semana_de_conclusao

                                elif deals[deal_id]['closed_date'] <= closed_date:
                                    deals[deal_id]['closed_date'] = closed_date
                                    try:
                                        semana_de_conclusao = datetime.strptime(str(deals[deal_id]['closed_date']).split('T')[0], '%Y-%m-%d')
                                        semana_de_conclusao = int(semana_de_conclusao.strftime("%U")) + 1
                                    except:
                                        semana_de_conclusao = None

                                    deals[deal_id]['semana_de_conclusao'] = semana_de_conclusao

                                if deals[deal_id]['semana_de_conclusao'] != None and deals[deal_id]['semana_de_abertura'] != None:
                                    deals[deal_id]['semanas_em_aberto_deal'] = deals[deal_id]['semana_de_conclusao'] - deals[deal_id]['semana_de_abertura']

                                
                                    
                            deals[deal_id]['qtd_devolvida'] += qtd_devolvida

                            if deals[deal_id]['qtd_prevista'] == deals[deal_id]['qtd_devolvida']:
                                deals[deal_id]['status_devolucao'] = 'Concluido'

                            

            df_deals = []
            cols_df = ['deal_id', 'data_abertura_do_deal', 'classe_do_pedido', 'closed_date', 'qtd_prevista', 'qtd_devolvida', 'status_devolucao', \
                       'semana_de_abertura', 'semana_de_conclusao', 'semanas_em_aberto_deal']
            for i in deals:
                df_deals.append([ \
                    i, deals[i]['data_abertura_do_deal'], deals[i]['classe_do_pedido'], deals[i]['closed_date'], deals[i]['qtd_prevista'],\
                    deals[i]['qtd_devolvida'], deals[i]['status_devolucao'] ,deals[i]['semana_de_abertura'], deals[i]['semana_de_conclusao'], deals[i]['semanas_em_aberto_deal']\
                    ])
            
            df_deals = pd.DataFrame.from_records(df_deals, columns=cols_df)

        #df_deals.to_csv('test.csv')
        return {
            'df_deals' : df_deals,
            'base' : base_de_dados
        }
    
    def estruturacao_coHorts(dataframe):
        tamanho_dos_eixos =dataframe['semana_de_abertura'].max() if dataframe['semana_de_abertura'].max() > dataframe['semana_de_conclusao'].max() else dataframe['semana_de_conclusao'].max()
        
        # constroi eixo Y
        dados_coHort = []
        for cont, y in enumerate( range( 1, int(tamanho_dos_eixos) + 1 ) ):
            # inicializa variaveis pré-definidas das semanas
            acumulado_deal_semana, acumulado_dispositivos_semana = 0, 0

            # Controi eixo X usando o contador que subtrai 1 a cada linha adicionada ao eixo Y
            for x in range( 0, (int(tamanho_dos_eixos) + 1 ) - cont ): 
                filtro = (dataframe['semana_de_abertura'] == y) & ( dataframe['semanas_em_aberto_deal'] == x ) & (dataframe['status_devolucao'] == 'Concluido')
                df_semana = dataframe[filtro]
                if len(df_semana) == 0:
                    deals_concluidos, dispositivos_concluidos = 0, 0

                else:
                    deals_concluidos = df_semana['deal_id'].count()
                    dispositivos_concluidos = df_semana['qtd_devolvida'].sum()
                    filtro = (dataframe['semana_de_abertura'] == y)
                    df_semana = dataframe[filtro]
                    acumulado_deal_semana = acumulado_deal_semana + (( deals_concluidos / df_semana['deal_id'].count()) * 100 )
                    acumulado_dispositivos_semana = acumulado_dispositivos_semana + (( dispositivos_concluidos / df_semana['qtd_prevista'].sum() ) * 100 )
                    
                dados_coHort.append([ y, x, deals_concluidos, dispositivos_concluidos, round(acumulado_deal_semana, 1), round(acumulado_dispositivos_semana, 1) ])
                    

        cols_df = ['semana_de_abertura', 'semana_em_relacao_ao_deal', 'qtd_deals_concluidos', 'qtd_disp_concluidos', 'per_acum_deal_semana', 'per_acum_disp_semana']
        dados_coHort = pd.DataFrame(dados_coHort, columns=cols_df)
        
        return {
        'coHort_deal' : dados_coHort.pivot_table(values='qtd_deals_concluidos', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum'),
        'coHort_deal_acum' : dados_coHort.pivot_table(values='per_acum_deal_semana', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum')
        }    
        
    def tabela_resumida(dataframe):
        semanas = dataframe['semana_de_abertura'].max()
        lista_results = []
        for i in range( 1, int(semanas) + 1):
            data = dataframe[ (dataframe['semana_de_abertura'] == i)]
            qtd_deals = data['deal_id'].count()
            concluidos = data[(data['status_devolucao'] == 'Concluido')]
            deals_concluidos = concluidos['deal_id'].count()
            percet_deal_efetivado = f'{round((deals_concluidos / qtd_deals) * 100, 2)}%'
            qtd_dispo_concluidos = concluidos['qtd_devolvida'].sum()
            qtd_disp_previsto = data['qtd_prevista'].sum()
            percent_disp = f'{ round((qtd_dispo_concluidos/qtd_disp_previsto) *100, 2) }%'
            semana_deal = f'Semana {i}'
            lista_results.append([semana_deal, deals_concluidos, qtd_deals, percet_deal_efetivado, qtd_dispo_concluidos, qtd_disp_previsto, percent_disp])
            
        cols_df = ['Semana de Abertura do Deal', 'Qtd. Deals Concluídos', 'Qtd. Total de Deals Abertos', '% de Deals Finalizados', 'Qtd. de Dispositivos Concluídos',\
                    'Qtd. de Dispositivos Previsto', '% de Dispositivos Concluídos']
        df_resumo = pd.DataFrame.from_records(lista_results, columns=cols_df, index='Semana de Abertura do Deal')
        
        #st.write(df_resumo) 
        #dataframe = dataframe.pivot(values=['deal_id', 'qtd_prevista', 'qtd_devolvida'], index='semana_de_abertura', aggfunc=['count', 'sum', 'sum'])

    def estrutura_base_dispositivos(dataframe, classes_para_filtro, status_concluidos):
        deals = {}
        for cont, i in enumerate(dataframe):
            if cont > 0:
                data_abertura_do_deal = i[8]
                classe_do_pedido = i[9]
                if classe_do_pedido in classes_para_filtro:
                    closed_date = i[5]
                    try:
                        qtd_prevista = int(i[6])
                    except:
                        qtd_prevista = None
                    try:
                        qtd_devolvida = int(i[7])
                    except:
                        qtd_devolvida = None
                    status_devolucao = i[3]

                    try:
                        semana_de_abertura = datetime.strptime(str(data_abertura_do_deal).split('T')[0], '%Y-%m-%d')
                        semana_de_abertura = int(semana_de_abertura.strftime("%U")) + 1
                    except:
                        semana_de_abertura = None

                    try:
                        semana_de_conclusao = datetime.strptime(str(closed_date).split('T')[0], '%Y-%m-%d')
                        semana_de_conclusao = int(semana_de_conclusao.strftime("%U")) + 1
                        semanas_em_aberto_deal = semana_de_conclusao - semana_de_abertura
                    except:
                        semana_de_conclusao = None
                    
                    if (qtd_devolvida != None or qtd_prevista != None):
                        if status_devolucao in status_concluidos:
                            status = 'Concluido'
                        else:
                            status = 'Pendente'
                        

                        deals[cont] = {
                            'data_abertura_do_deal' : data_abertura_do_deal,
                            'classe_do_pedido' : classe_do_pedido,
                            'closed_date' : closed_date,
                            'qtd_prevista' : qtd_prevista,
                            'qtd_devolvida' : qtd_devolvida,
                            'status_devolucao' : status,
                            'semana_de_abertura' : semana_de_abertura,
                            'semana_de_conclusao' : semana_de_conclusao,
                            'semanas_em_aberto_deal' : semanas_em_aberto_deal,
                            'status' : status,
                            'deal_id' : str(i[1])
                        }
        
        df_deals = []
        cols_df = ['deal_id', 'data_abertura_do_deal', 'classe_do_pedido', 'closed_date', 'qtd_prevista', 'qtd_devolvida', 'status_devolucao', \
                    'semana_de_abertura', 'semana_de_conclusao', 'semanas_em_aberto_deal']
        for i in deals:
            df_deals.append([ \
                deals[i]['deal_id'], deals[i]['data_abertura_do_deal'], deals[i]['classe_do_pedido'], deals[i]['closed_date'], deals[i]['qtd_prevista'],\
                deals[i]['qtd_devolvida'], deals[i]['status_devolucao'] ,deals[i]['semana_de_abertura'], deals[i]['semana_de_conclusao'], deals[i]['semanas_em_aberto_deal']\
                ])
        
        df_deals = pd.DataFrame.from_records(df_deals, columns=cols_df)
        df_deals.to_csv('test.csv')
        return df_deals

    def estruturacao_coHortsDisp(dataframe):
        tamanho_dos_eixos =dataframe['semana_de_abertura'].max() if dataframe['semana_de_abertura'].max() > dataframe['semana_de_conclusao'].max() else dataframe['semana_de_conclusao'].max()
        
        # constroi eixo Y
        dados_coHort = []
        for cont, y in enumerate( range( 1, int(tamanho_dos_eixos) + 1 ) ):
            # inicializa variaveis pré-definidas das semanas
            acumulado_deal_semana, acumulado_dispositivos_semana = 0, 0

            # Controi eixo X usando o contador que subtrai 1 a cada linha adicionada ao eixo Y
            for x in range( 0, (int(tamanho_dos_eixos) + 1 ) - cont ): 
                filtro = (dataframe['semana_de_abertura'] == y) & ( dataframe['semanas_em_aberto_deal'] == x ) & (dataframe['status_devolucao'] == 'Concluido')
                filtro2 =(dataframe['semana_de_abertura'] == y)
                df_semana = dataframe[filtro]
                df_semana2 = dataframe[filtro2]
                sumDisp = 0
                listaDeals = []
                for i in df_semana2['deal_id'].unique():
                    if str(i) in listaDeals:
                        pass
                    else:
                        listaDeals.append(str(i))
                        deal = df_semana2[(df_semana2['deal_id'] == i)]
                        deal = deal['qtd_prevista'].mean()
                        sumDisp += deal

                if len(df_semana) == 0:
                    deals_concluidos, dispositivos_concluidos = 0, 0

                else:
                    deals_concluidos = 0
                    dispositivos_concluidos = df_semana['qtd_devolvida'].sum()
                    filtro = (dataframe['semana_de_abertura'] == y)
                    df_semana = dataframe[filtro]
                    acumulado_deal_semana = acumulado_deal_semana + (( deals_concluidos / df_semana['deal_id'].count()) * 100 )
                    acumulado_dispositivos_semana += ((dispositivos_concluidos / sumDisp) * 100 )
                    
                dados_coHort.append([ y, x, deals_concluidos, dispositivos_concluidos, round(acumulado_deal_semana, 1), round(acumulado_dispositivos_semana, 1) ])
                    

        cols_df = ['semana_de_abertura', 'semana_em_relacao_ao_deal', 'qtd_deals_concluidos', 'qtd_disp_concluidos', 'per_acum_deal_semana', 'per_acum_disp_semana']
        dados_coHort = pd.DataFrame(dados_coHort, columns=cols_df)
        
        return {
        'coHort_deal' : dados_coHort.pivot_table(values='qtd_disp_concluidos', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum'),
        'coHort_deal_acum' : dados_coHort.pivot_table(values='per_acum_disp_semana', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='mean')
        }

    async def perguntas(dataFrameDeal, pergunta, filtrar_classe):
        cols = []
        linhas = []
        for cont, i in enumerate(dataFrameDeal):
            if cont == 0:
                for item in i:
                    cols.append(str(item))
            else:
                data_abertura_do_deal = i[8]
                closed_date = i[5]
                try:
                    try:
                        semana_de_abertura = datetime.strptime(str(data_abertura_do_deal).split('T')[0], '%Y-%m-%d')
                    except:
                        semana_de_abertura = datetime.strptime(str(data_abertura_do_deal), '%Y-%m-%d')
                    semana_de_abertura = f'Aberto na Semana {int(semana_de_abertura.strftime("%U")) + 1}'
                except:
                    semana_de_abertura = None
                
                try:
                    semana_de_conclusao = datetime.strptime(str(closed_date).split('T')[0], '%Y-%m-%d')
                    semana_de_conclusao = f'Aberto na Semana {int(semana_de_conclusao.strftime("%U")) + 1}'
                except:
                    semana_de_conclusao = None
                item = i
                item.extend([semana_de_abertura, semana_de_conclusao])
                linhas.append(item)
        
        cols.extend(['semana de abertura', 'semana de conclusao'])
        df = pd.DataFrame.from_records(linhas, columns=cols)
        
        if filtrar_classe != "Todas as Classes":
            df = df[(df['supply__devolucao__tipo'] == filtrar_classe)]

        csv = df.to_html()
       
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyCsVCgLULGsI1M_faQdQhLdMyGOVhJPoiw"
        payload = json.dumps({
        "contents": [
            {
            "parts": [
                {
                "text": f'Com base na tabela do html {csv} {pergunta}?'
                }
            ]
            }
        ]
        })
        headers = {
        'Content-Type': 'application/json'
        }
        with requests.Session() as session:
            response = session.post( url, headers=headers, data=payload).json()
            try:
                response = response['candidates'][0]['content']['parts'][0]['text']
            except:
                response = "Não foi possível atender a solicitação, tente novamente."
        st.write(response)


class Definicao_das_Views():
    # Defini configurações do streamlit
    def configuracao_pagina_streamlit():
        st.set_page_config(layout="wide")
        st.set_option('deprecation.showPyplotGlobalUse', False)
    
    def autenticacao():
        headers = {
        'apikey': st.secrets["db_username"]
        }
        
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
            return True
        
        elif st.session_state["authentication_status"] is False:
            st.error('Usuário/Senha is inválido')
            return False 
    
    def definicao_pipeline():
        pipeline = st.selectbox(label='Selecione a Pipeline', options=['Devolução', 'Instalação'])
        return pipeline

    def constroi_coHort(base, largura : int, altura : int, descricao_base : str, percentil : bool):
        f, ax = plt.subplots(figsize=(largura, altura))
        cmap = ['#e67c73', '#f8d567', '#f1d469', '#f1d469', '#e2d26c', '#dad06e', '#d3cf6f', '#cbce71', '#c4cd72', '#bccc74', '#b5ca76',\
                '#aec977', '#a6c879', '#9fc77a', '#97c67c', '#90c47e', '#88c37f', '#81c281', '#79c182', '#72c084', '#6abe86']
        
        st.html('<hr>')
        st.html(f'<h3 style="color : #666666">{descricao_base}</h3>')
        monthly_sessions = sns.heatmap(base, 
                            annot=True,
                            annot_kws={"size": 10, "color" : "black"}, 
                            linewidths=0.5, 
                            ax=ax, 
                            cmap=cmap, 
                            square=False,
                            fmt='.3g'
                            )
        if percentil:
            for t in ax.texts: 
                texto = t.get_text()
                if str(texto).find(".") < 1:
                    texto = texto + '.0'
                
                t.set_text( texto + " %")

        ax.set_xlabel("Semana em relação ao Deal",fontsize=12)
        ax.set_ylabel("Semanas de Abertura",fontsize=12)
        
        plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = False, labeltop=True)
        st.pyplot(plt.show())

    def propriedades_de_exibicao_coHort():
        # Filtros    
        largura = st.sidebar.select_slider(
            "tamanho do eixo X em relação ao eixo Y",
            options=range(28, 100),
            value=(28))

        altura = st.sidebar.select_slider(
            "tamanho do eixo Y em relação ao eixo x",
            options=range(0, 100),
            value=(8))
    
        return [altura, largura]
    
    def filtra_por_classe(dataframe, pipeline):
        classes = ["Todas as Classes"]
        classes.extend(dataframe['classe_do_pedido'].unique().tolist())
        filtrar_classe = st.sidebar.selectbox("Filtrar por Classe do Pedido:", classes)
        if filtrar_classe != "Todas as Classes":
            df = dataframe[(dataframe['classe_do_pedido'] == filtrar_classe)]
            st.html(f'<h1 style="color : #666666">Completude - {pipeline} - {filtrar_classe}</h1>')
            return {
                'df' : df,
                'filtro' : str(filtrar_classe)
            }
        else:
            st.html(f'<h1 style="color : #666666">Completude - {pipeline}</h1>')
            return {
                'df' : dataframe,
                'filtro' : str(filtrar_classe)
            }
        
    def filtra_por_classe_disp(dataframe, filtrar_classe):
        if filtrar_classe != "Todas as Classes":
            df = dataframe[(dataframe['classe_do_pedido'] == filtrar_classe)]
            return df
        else:
            return dataframe

class Executa_app(Estruturacao_dos_dados, Definicao_das_Views):
    def __init__(self) -> None:
        Definicao_das_Views.configuracao_pagina_streamlit()
        if Definicao_das_Views.autenticacao():
            pipeline = Definicao_das_Views.definicao_pipeline()
            if pipeline == 'Devolução':
                classes = ['Troca', 'Abandono total', 'Abandono parcial', 'Upgrade', 'Lost piloto', 'Piloto parcial']
                status_concluidos = ['Concluido', 'Devolução Cancelada']
            else:
                classes = ['Primeira compra', 'Upsell', 'Upgrade', 'Piloto', 'Troca', 'Downgrade', 'Troca entre veículos']
                status_concluidos = ['Instalado', 'Instalação Cancelada']
            
            try:
                df = Estruturacao_dos_dados.obtencao_dos_dados(classes, status_concluidos, pipeline)
                base = df['base']
                df_disp = Estruturacao_dos_dados.estrutura_base_dispositivos(df['base'], classes, status_concluidos)
                df = Definicao_das_Views.filtra_por_classe(df['df_deals'], pipeline)
                filtro = df['filtro']
                df_disp = Definicao_das_Views.filtra_por_classe_disp(df_disp, df['filtro'])

                

                df = df['df']
                # Descrição dos coHorts gerados:
                #- coHort_deal : realiza a contagem dos deals por semana
                #- coHort_deal_acum : divide total de deals da semana de conclusão em relação ao deal ao total da semana de conclusão
                #- coHort_disp : realiza soma dos dispositivos
                #- coHort_disp_acum : divide total de dispositivos da semana de conclusão em relação ao dispositivos ao total da semana de conclusão
                
                
                Estruturacao_dos_dados.tabela_resumida(df)
                response = Estruturacao_dos_dados.estruturacao_coHorts(df)
                responseDisp = Estruturacao_dos_dados.estruturacao_coHortsDisp(df_disp)
                propriedades = Definicao_das_Views.propriedades_de_exibicao_coHort()
                Definicao_das_Views.constroi_coHort(response['coHort_deal'], propriedades[1], propriedades[0], 'Fechamento por Deal Id', percentil=False)
                Definicao_das_Views.constroi_coHort(response['coHort_deal_acum'], propriedades[1], propriedades[0], '% de Fechamento por Deal Id', percentil=True)

                Definicao_das_Views.constroi_coHort(responseDisp['coHort_deal'], propriedades[1], propriedades[0], 'Fechamento por Dispositivo', percentil=False)
                Definicao_das_Views.constroi_coHort(responseDisp['coHort_deal_acum'], propriedades[1], propriedades[0], '% de Fechamento por Dispositivo', percentil=True)
                if True:#st.checkbox('Deseja exibir a base de dados'):
                    st.dataframe(df)
            except:
                st.html("<h3>Não há dados!!!</h3>")

Executa_app()