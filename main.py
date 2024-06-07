import requests, json
import pandas as pd
from datetime import datetime

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

filtros = (df['Quantidade Devolução - Calculado - Total'] != '(No value)') & (df['Ticket status'].isin(['Concluido', 'Devolução Cancelada'])) &\
    (df['CO - Quantidade - Calculado - Total de dispositivos para devolução'] != '(No value)') & \
        (df['Pedido data - Daily'] != '(No value)') & (df['supply__devolucao__tipo'].isin(classes_a_exibir))

df = df[filtros]

lista = df.values.tolist()

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

list_df = []
for i in dic_lista:
    data_de_solicitacao = datetime.strptime(str(dic_lista[i]['data_de_solicitacao']).split('T')[0], '%Y-%m-%d')
    semana_solicitacao = int(data_de_solicitacao.strftime("%U")) + 1
    data_conclusao = dic_lista[i]['data_conclusão']
    semana_conclusao = int(data_conclusao.strftime("%U")) + 1
    semanas_em_aberto = abs(int(semana_conclusao) - int(semana_solicitacao))

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

