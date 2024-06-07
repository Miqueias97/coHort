import requests, json
import pandas as pd
from datetime import datetime
import streamlit as st
import streamlit_authenticator as stauth
import seaborn as sns
import matplotlib.pyplot as plt

class Defini_Views():
    # Defini configurações do streamlit
    #st.set_option('deprecation.showPyplotGlobalUse', False)
    def configura_pagina_streamlit():
        st.set_page_config(layout="wide")

class Manipulacao_do_dados():
    # constroi df com base nos dados armazenados no sheets e filtra baseado nas classes de interesse
    def base_sheets(classes_para_filtro, status_concluidos):
        # obtem dados e agrupa os Deals
        url = 'https://script.google.com/macros/s/AKfycbwOFDUXCrRtMEQY4GXJ_jwp9x9Lp7NF3n06s9uU0NVF268iQo0jGvENvPBWHvWTalu4/exec'
        deals = {}
        with requests.Session() as session:
            for i, data in enumerate(requests.get(url).json()['status']):
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

                                elif deals[deal_id]['closed_date'] < closed_date:
                                    deals[deal_id]['closed_date'] = closed_date
                                    try:
                                        semana_de_conclusao = datetime.strptime(str(deals[deal_id]['closed_date']).split('T')[0], '%Y-%m-%d')
                                        semana_de_conclusao = int(semana_de_conclusao.strftime("%U")) + 1
                                    except:
                                        semana_de_conclusao = None

                                deals[deal_id]['semana_de_conclusao'] = semana_de_conclusao
                                if deals[deal_id]['semana_de_conclusao'] != None and deals[deal_id]['semana_de_abertura'] != None:
                                    semanas_em_aberto_deal = semana_de_conclusao - semana_de_abertura

                                
                                    
                            deals[deal_id]['qtd_devolvida'] += qtd_devolvida

                            if deals[deal_id]['qtd_prevista'] == deals[deal_id]['qtd_devolvida']:
                                status_devolucao = 'Concluido'

            df_deals = []
            cols_df = ['deal_id', 'data_abertura_do_deal', 'classe_do_pedido', 'closed_date', 'qtd_prevista', 'qtd_devolvida', 'status_devolucao', \
                       'semana_de_abertura', 'semana_de_conclusao', 'semanas_em_aberto_deal']
            for i in deals:
                df_deals.append([ \
                    i, deals[i]['data_abertura_do_deal'], deals[i]['classe_do_pedido'], deals[i]['closed_date'], deals[i]['qtd_prevista'],\
                    deals[i]['qtd_devolvida'], deals[i]['status_devolucao'] ,deals[i]['semana_de_abertura'], deals[i]['semana_de_conclusao'], deals[i]['semanas_em_aberto_deal']\
                    ])
            
            df_deals = pd.DataFrame.from_records(df_deals, columns=cols_df)

        return df_deals
    
    def estrutura_coHorts(dataframe):
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
                    filtro = (dataframe['semana_de_abertura'] == y) & (dataframe['status_devolucao'] == 'Concluido')
                    df_semana = dataframe[filtro]
                    acumulado_deal_semana = acumulado_deal_semana + (( deals_concluidos / df_semana['deal_id'].count()) * 100 )
                    acumulado_dispositivos_semana = acumulado_dispositivos_semana + (( dispositivos_concluidos / df_semana['qtd_devolvida'].sum() ) * 100 )
                    
                dados_coHort.append([ y, x, deals_concluidos, dispositivos_concluidos, round(acumulado_deal_semana, 2), round(acumulado_dispositivos_semana, 2) ])
                    

        cols_df = ['semana_de_abertura', 'semana_em_relacao_ao_deal', 'qtd_deals_concluidos', 'qtd_disp_concluidos', 'per_acum_deal_semana', 'per_acum_disp_semana']
        dados_coHort = pd.DataFrame(dados_coHort, columns=cols_df)
        return {
        'coHort_deal' : dados_coHort.pivot_table(values='qtd_deals_concluidos', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum'),
        'coHort_deal_acum' : dados_coHort.pivot_table(values='per_acum_deal_semana', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum'),
        'coHort_disp' : dados_coHort.pivot_table(values='qtd_disp_concluidos', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum'),
        'coHort_disp_acum' : dados_coHort.pivot_table(values='per_acum_disp_semana', index='semana_de_abertura', columns='semana_em_relacao_ao_deal', aggfunc='sum')
        }    
        



class Executa_app(Manipulacao_do_dados):
    def __init__(self) -> None:
        Defini_Views.configura_pagina_streamlit()

        classes = ['Troca', 'Abandono total', 'Abandono parcial', 'Upgrade', 'Lost piloto', 'Piloto parcial']
        status_concluidos = ['Concluido', 'Devolução Cancelada']


        df = Manipulacao_do_dados.base_sheets(classes, status_concluidos)

        """
        Descrição dos coHorts gerados:
        - coHort_deal : realiza a contagem dos deals por semana
        - coHort_deal_acum : 
        - coHort_disp
        - coHort_disp_acum
        """

        response = Manipulacao_do_dados.estrutura_coHorts(df)

        
        
        




Executa_app()

