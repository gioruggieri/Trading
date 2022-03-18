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
import talib


api_key = ""
api_secret = ""

client = Client(api_key, api_secret)

url = 'https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products'

dateFrom = "0.5 hour ago UTC" 
dateoneminute = "1 minute Ago UTC" 
interval = Client.KLINE_INTERVAL_1MINUTE

while True:
    crypto = pd.DataFrame(columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Crypto', 'EMA223', 'MACD', 'MarkCap', 'count_up', 'count_down', 'lowest', 'highest'])
    
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
        klines = client.get_historical_klines(crypto.iloc[j]['Crypto'], interval, dateFrom)
        coin = pd.DataFrame(klines)
        coin = coin.iloc[:, 0:6]
        coin.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        coin['Time'] = [datetime.fromtimestamp(float(time)/1000) for time in coin['Time']]
        coin.insert(6, "SupT", True)
        coin.insert(0, 'Crypto', crypto.iloc[j]['Crypto'])
        coin = coin.astype({'Close': 'float16', 'High': 'float16', 'Low': 'float16'})
        coin_8h = coin_8h.append(coin)
    grouped = coin_8h.groupby('Crypto')
    for name, group in grouped:
        group['SAR'] = talib.SAR(group['High'], group['Low'], 0.05, 1.2)
        if (group.iloc[-1]["SAR"] < group.iloc[-1]["Close"]) and (group.iloc[-2]["SAR"] > group.iloc[-2]["Close"]):
            print(name, '=', group.iloc[-1]["Crypto"], '  TIME = ', group.iloc[-1]['Time'].strftime("%m/%d/%Y, %H:%M:%S"))
        
        
