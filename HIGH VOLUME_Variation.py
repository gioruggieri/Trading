import time
import pandas as pd
import winsound
from datetime import datetime
import json
import requests
import subprocess
from binance.client import Client
from binance import exceptions
import pandas_ta as ta
from sklearn.preprocessing import MinMaxScaler


api_key = ""
api_secret = ""

client = Client(api_key, api_secret)

url = 'https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products'

dateFrom = "0.5 hour ago UTC" 
dateoneminute = "1 minute Ago UTC" 
interval = Client.KLINE_INTERVAL_1MINUTE

while True:
    crypto = pd.DataFrame(columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Crypto', 'Volume_Variation'])
    
    mkc = pd.DataFrame(json.loads(requests.get(url).text))
    
        
    for i in range(len(mkc)-1):
        if mkc.data[i]['cs'] == None:
                continue
        if mkc.data[i]['q'] == 'USDT':
            #crypto = crypto.append({'MarkCap' : mkc.data[i]['cs'] * float(mkc.data[i]['c']), 'Crypto' : mkc.data[i]['s']}, ignore_index=True)#ordino per marketcap
            crypto = crypto.append({'MarkCap' : float(mkc.data[i]['qv']), 'Crypto' : mkc.data[i]['s']}, ignore_index=True) # ordinare per volume 24h usdt
    crypto = crypto.sort_values(by=['MarkCap'], ascending=False)        
    crypto = crypto.head(100)
    crypto = crypto.reset_index(drop=True)
    
    coin_8h = pd.DataFrame()
    
    print('_________________________________________________________________')
    for j in range(len(crypto)-1):
        try:
            klines = client.get_klines(symbol=crypto.iloc[j]['Crypto'],interval=Client.KLINE_INTERVAL_1MINUTE,limit=(2))
        except exceptions.BinanceAPIException as e:
            print(e)
            print('Something went wrong.' + str(datetime.now))
            time.sleep(1)
            client = Client(api_key, api_secret)
            continue
        
        coin = pd.DataFrame(klines)
        coin = coin.iloc[:, 0:6]
        coin.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        coin['Time'] = [datetime.fromtimestamp(float(time)/1000) for time in coin['Time']]
        coin.insert(0, 'Crypto', crypto.iloc[j]['Crypto'])
        if float(coin.iloc[1]['Volume']) == 0 or float(coin.iloc[0]['Volume']) == 0:
            coin.insert(5, 'Volume_Variation', 0)
        else:
            coin.insert(5, 'Volume_Variation', (((float(coin.iloc[1]['Volume'])*100)-100)/float(coin.iloc[0]['Volume'])))
        coin_8h = coin_8h.append(coin)
    grouped = coin_8h.groupby('Crypto')
    for name, group in grouped:
        crypto.at[crypto.loc[crypto['Crypto']==name].index[0], 'Volume_Variation'] = group.iloc[-1]['Volume_Variation']
        crypto.at[crypto.loc[crypto['Crypto']==name].index[0], 'Time'] = group.iloc[-1]['Time']
    #coin_8h = coin_8h.reset_index(drop=True)
    print(crypto.nlargest(20, 'Volume_Variation'))
    
