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
                    
                    deal_id = data[1]
                    status = data[3]
                    data_abertura_do_deal = data[8]
                    classe_do_pedido = data[9]
                    try:
                        qtd_prevista = int(data[6])
                    except:
                        qtd_prevista = None
                    if status in status_concluidos and qtd_prevista != None:
                        closed_date = data[5]
                        try:
                            qtd_devolvida = int(data[7])
                        except:
                            qtd_devolvida = 0
                    else:
                        closed_date, qtd_devolvida = None, 0 
                    
                    status_devolucao = 'Pendente'
                    if deal_id not in deals:
                        if qtd_prevista == qtd_devolvida:
                            status_devolucao = 'Concluido'
                        deals[deal_id] = {
                        'data_abertura_do_deal' : data_abertura_do_deal,
                        'classe_do_pedido' : classe_do_pedido,
                        'closed_date' : closed_date,
                        'qtd_prevista' : qtd_prevista,
                        'qtd_devolvida' : qtd_devolvida,
                        'status_devolucao' : status_devolucao
                    }
                    else:
                        if closed_date != None:
                            # substitui data anterior caso ela seja None
                            if deals[deal_id]['closed_date'] == None:
                                deals[deal_id]['closed_date'] = closed_date
                            elif deals[deal_id]['closed_date'] < closed_date:
                                deals[deal_id]['closed_date'] = closed_date
                                
                        deals[deal_id]['qtd_devolvida'] += qtd_devolvida

                        if deals[deal_id]['qtd_prevista'] == deals[deal_id]['qtd_devolvida']:
                            status_devolucao = 'Concluido'
            
        return deals
                    

                



class Executa_app(Manipulacao_do_dados):
    def __init__(self) -> None:
        classes = ['Troca', 'Abandono total', 'Abandono parcial', 'Upgrade', 'Lost piloto', 'Piloto parcial']
        status_concluidos = ['Concluido', 'Devolução Cancelada']
        df = Manipulacao_do_dados.base_sheets(classes, status_concluidos)
        print(df)
        




Executa_app()

