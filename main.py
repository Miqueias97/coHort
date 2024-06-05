import pandas as pd
from datetime import datetime

df = pd.read_excel(r'hubspot-custom-report-devolucoes-2024-06-05.xls')

# Filtra Dataframe removendo No value
filtros = (df['Quantidade Devolução - Calculado - Total'] != '(No value)') & (df['Ticket status'].isin(['Concluido', 'Devolução Cancelada'])) &\
      (df['CO - Quantidade - Calculado - Total de dispositivos para devolução'] != '(No value)')
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
        data_realizacao = datetime.strptime(i[5], "%Y-%m-%d")
    except:
        pass

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

colunas = ['Deal Id', 'data_de_solicitacao', 'qtd_prevista', 'qtd_realizada', 'data_conclusão', 'classe', 'semana_solicitacao', 'semana_conclusao', 'semanas_em_aberto']
list_df = []
dia_da_semana = {
    0 : 'Segunda',
    1 : 'Terça',
    2 : 'Quarta',
    3 : 'Quinta',
    4 : 'Sexta',
    5 : 'Sábado',
    6 : 'Domingo'
}
for i in dic_lista:
    if dic_lista[i]['qtd_prevista'] == dic_lista[i]['qtd_realizada']:
        # Verifica dia da semana de solicitação
        data_de_solicitacao = datetime.strptime(dic_lista[i]['data_de_solicitacao'], '%Y-%m-%d')
        semana_solicitacao = data_de_solicitacao.strftime("%U")
        data_conclusao = dic_lista[i]['data_conclusão']
        semana_conclusao = data_conclusao.strftime("%U")
        semanas_em_aberto = abs(int(semana_conclusao) - int(semana_solicitacao))
        

        list_df.append( [i, dic_lista[i]['data_de_solicitacao'], dic_lista[i]['qtd_prevista'], dic_lista[i]['qtd_realizada'],\
                          dic_lista[i]['data_conclusão'], dic_lista[i]['classe'], semana_solicitacao, semana_conclusao, semanas_em_aberto ] )


df = pd.DataFrame.from_records(list_df, columns=colunas)

tabela_dinamica = df.pivot_table(values='Deal Id', index='semana_solicitacao', columns='semanas_em_aberto', aggfunc='count', fill_value=0) 
tabela_dinamica.to_csv('dinamica.csv')
# Grafico
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

plt.figure(figsize=(16, 10))
plt.title('Cohorts Fechamento de tickets Devolução', fontsize = 14)
valor_Maximo = tabela_dinamica.values.max()

sns.heatmap(tabela_dinamica, annot = True,vmin = 0.0, vmax =valor_Maximo,cmap="YlGnBu", fmt='g')
plt.ylabel('Semana de Abertura')
plt.xlabel('Semanas até o Fechamento')
fig = plt.figure()
st.write(fig)