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
        status = 'Cocluído'
    else:
        status = 'Pendente'
        
    
    list_df.append( [i, dic_lista[i]['data_de_solicitacao'], dic_lista[i]['qtd_prevista'], dic_lista[i]['qtd_realizada'],\
                    dic_lista[i]['data_conclusão'], dic_lista[i]['classe'], semana_solicitacao, semana_conclusao, semanas_em_aberto, status ] )
    

colunas = ['Deal Id', 'data_de_solicitacao', 'qtd_prevista', 'qtd_realizada', 'data_conclusão', 'classe', 'semana_solicitacao', 'semana_conclusao', 'semanas_em_aberto', 'status']

df = pd.DataFrame.from_records(list_df, columns=colunas)

# inicia contrução do coHort
maior_valor = (df['semana_solicitacao'].values.max() if df['semana_solicitacao'].values.max() >= df['semana_conclusao'].values.max() \
               else df['semana_conclusao'].values.max()) + 1

estrutura_coHort = {}
for cont, y in enumerate(range(1, maior_valor)):

    total_de_deals, total_de_dispositivos = 0 , 0

    for x in range(0, maior_valor - cont):
        filtro_df = df[(df.semana_solicitacao == y) & (df.semanas_em_aberto == x)]
        dic_clase = {}
        if len(filtro_df) > 0:
            classes = filtro_df.classe.unique().tolist()
            
            for classe in classes:
                filtro_por_classe = filtro_df[(filtro_df.classe) == classe]  
                if classe not in dic_clase:
                    dic_clase[classe] = {
                        'Semana Deal' : y,
                        'Semana em relação ao Deal' : x,
                        'qtd_deal' : filtro_por_classe['Deal Id'].count(),
                        'acumulado' : filtro_df['Deal Id'].count(),
                        'qtd_realizada' : filtro_por_classe['qtd_realizada'].sum(),
                        'acumulado_disp' : '',
                        'qtd_prevista' : filtro_df['qtd_prevista'].sum()
                    }
                else:
                    dic_clase[classe] = 'ok'
                    
        else:
            dic_clase['zero'] = {
                'Semana Deal' : y,
                'Semana em relação ao Deal' : x,
                'qtd_deal' : 0,
                'acumulado' : '',
                'qtd_realizada' : 0,
                'acumulado_disp' : '',
                'qtd_prevista' : 0
            }

        estrutura_coHort[str(f'{y} : {x}')] = dic_clase
        break
        
print(estrutura_coHort)