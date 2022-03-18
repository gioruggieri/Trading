# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 08:50:15 2021

@author: gaiar
"""
import pandas as pd
import matplotlib as plt
import datetime as dt
import json
import requests
import networkx as nx
from binance.client import Client
import time
start_time = time.time()



api_key = ""
api_secret = ""


client = Client(api_key, api_secret)

url = 'https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products'

dateFrom = "30 min ago UTC" #"1 May, 2021"
interval = Client.KLINE_INTERVAL_1MINUTE

crypto = pd.DataFrame(columns=['name', 'MarkCap'])
mkc = pd.DataFrame(json.loads(requests.get(url).text))
for i in range(len(mkc)-1):
    if mkc.data[i]['cs'] == None:
            continue
    if mkc.data[i]['q'] == 'USDT':
        #crypto = crypto.append({'MarkCap' : mkc.data[i]['cs'] * float(mkc.data[i]['c']), 'name' : mkc.data[i]['s']}, ignore_index=True)
        crypto = crypto.append({'MarkCap' : float(mkc.data[i]['qv']), 'name' : mkc.data[i]['s']}, ignore_index=True) # ordinare per volume 24h usdt
crypto = crypto.sort_values(by=['MarkCap'], ascending=False)        
crypto = crypto.head(100)
crypto = crypto.reset_index(drop=True)
#crypto.to_csv('lista_crypto')
#crypto = crypto.append({'name' : 'FTMUSDT'}, ignore_index=True)
 
dati = pd.DataFrame()
     
#KLINE_INTERVAL_1MINUTE = '1m'
for j in range(len(crypto)-1):
    klines = client.get_historical_klines(crypto.name[j], interval, dateFrom)
    df = pd.DataFrame(klines)
    df = df.iloc[:, 0:6]
    df.columns = ['Time', 'open', 'high', 'low', 'close', 'volume']
    #df.index = [dt.datetime.fromtimestamp(x / 1000) for x in df.datetime]
    #dati = df
    df = pd.DataFrame(df.close)
    df.columns = [crypto.name[j]]
    dati = pd.concat([dati,df],axis=1)

  
#corr = dati_crypto.corr()
dati = dati.astype(float)
corr = dati.corr()
#corr.to_csv('d:/' + str(dt.date.today()) + '_Corr.csv', index=True)

#Find a subset, Filtered to no corellation to BTC, of no intra Correlation
#dati_toBTC = corr[(corr['BTCUSDT']<-0.8)].fillna("")
dati_toBTC = corr[(corr['BTCUSDT']>-0.1) & (corr['BTCUSDT']<0.1)].fillna("")

print("--- %s seconds ---" % (time.time() - start_time))

df_corr = corr
df_corr1 = df_corr.where((df_corr<0.5) & (df_corr>-0.5), 2)
df_corr1 = df_corr1.where((df_corr1==2), 1)
df_corr1 = df_corr1.where((df_corr1==1), 0)

G = nx.from_pandas_adjacency(df_corr1, create_using=nx.Graph)
maxc = nx.find_cliques(G)
lista_Crypto_Corr = max(maxc, key=len)
print("--- %s seconds ---" % (time.time() - start_time))
#Confronto con BTC delle crypto scorrelate
# crypto2 = [w.replace('USDT', 'BTC') for w in lista_Crypto_Corr]
# dati = pd.DataFrame()
# for j in range(len(crypto)-1):
#     try:
#         klines = client.get_historical_klines(crypto2[j], interval, dateFrom)
#         df = pd.DataFrame(klines)
#         df = df.iloc[:, 0:6]
#         df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
#         df.index = [dt.datetime.fromtimestamp(x / 1000) for x in df.datetime]
#         df = pd.DataFrame(df.close)
#         df.columns = [crypto2[j]]
#         dati = pd.concat([dati,df],axis=1)
#     except:
#         continue
    
#------------IMPLEMENTARE IL PLOT-------------

