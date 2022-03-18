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


api_key = ""
api_secret = ""

client = Client(api_key, api_secret)

url = 'https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products'

dateFrom = "8 hour ago UTC" 
dateoneminute = "1 minute Ago UTC" 
interval = Client.KLINE_INTERVAL_1MINUTE

crypto = pd.DataFrame(columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Crypto', 'EMA223', 'MarkCap', 'count_up', 'count_down', 'lowest', 'highest'])

mkc = pd.DataFrame(json.loads(requests.get(url).text))

for i in range(len(mkc)-1):
    if mkc.data[i]['cs'] == None:
            continue
    if mkc.data[i]['q'] == 'USDT':
        crypto = crypto.append({'MarkCap' : mkc.data[i]['cs'] * float(mkc.data[i]['c']), 'Crypto' : mkc.data[i]['s']}, ignore_index=True)
crypto = crypto.sort_values(by=['MarkCap'], ascending=False)        
crypto = crypto.head(100)
crypto = crypto.reset_index(drop=True)
crypto['EMA223'] = 999999.9
crypto['count_up'] = 0
crypto['count_down'] = 0
crypto['lowest'] = 0.0
crypto['highest'] = 0.0

min_durata_Down = 180
min_durata_Up = 180
min_delta_Down = 9
min_delta_Up = 7
coin_8h = pd.DataFrame()
for j in range(len(crypto)-1):
    klines = client.get_historical_klines(crypto.iloc[j]['Crypto'], interval, dateFrom)
    coin = pd.DataFrame(klines)
    coin = coin.iloc[:, 0:6]
    coin.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    coin['Time'] = [datetime.fromtimestamp(float(time)/1000) for time in coin['Time']]
    coin.insert(6, "EMA223", True)
    coin.insert(0, 'Crypto', crypto.iloc[j]['Crypto'])
    coin_8h = coin_8h.append(coin)
grouped = coin_8h.groupby('Crypto')
for name, group in grouped:
    group["EMA223"] = ta.ema(group["Close"], length=223)
    crypto.at[crypto.loc[crypto['Crypto']==name].index[0], 'EMA223'] = group.iloc[-1]['EMA223']
    crypto.at[crypto.loc[crypto['Crypto']==name].index[0], 'Time'] = group.iloc[-1]['Time']
while True:
    t0 = time.time()
    for i in range(len(crypto)):
        try:
            klines = client.get_klines(symbol=crypto.iloc[i]['Crypto'],interval=Client.KLINE_INTERVAL_1MINUTE,limit=(1))
        except exceptions.BinanceAPIException as e:
            print(e)
            print('Something went wrong.' + str(datetime.now))
            time.sleep(1)
            client = Client(api_key, api_secret)
            continue
        

        df = pd.DataFrame(klines)
        df = df.iloc[:, 0:6]
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        df.insert(0, 'Crypto', True)
        #df.insert(1, 'EMA223', 999999)
        #df.iloc[0]['Crypto'] = crypto.iloc[i]['Crypto']
        crypto.iloc[i]['Time'] = [datetime.fromtimestamp(float(df.iloc[0]['Time']/1000))]
        if df.iloc[0]['Time'] == crypto.iloc[i]['Time']:
            continue
        crypto.at[i, 'Time'] = df.iloc[0]['Time']
        #print(df.iloc[0]['Time'],'--------', crypto.iloc[i]['Time'])
        if crypto.iloc[i]['EMA223'] == 999999.9:
            crypto.at[i, 'EMA223'] = df.iloc[0]['Close']
        else:
            crypto.at[i, 'EMA223'] = ((float(df.iloc[0]['Close']) - float(crypto.iloc[i]['EMA223'])) * 0.00893) + float(crypto.iloc[i]['EMA223'])
        #print('ema is: ', crypto.iloc[i]['EMA223'])
        # df["EMA223"] = ta.ema(df["Close"], length=223)
        # df = df.iloc[224:-1]
        
        if float(df.iloc[0]['High']) > float(crypto.iloc[i]['EMA223']) and crypto.iloc[i]['count_down'] >= min_durata_Down and (((float(df.iloc[0]['High']) / crypto.iloc[i]['lowest']) -1) * 100) > min_delta_Down:
                print('---------shouldLong----------', crypto.iloc[i]['Crypto'], df.iloc[0]['Time'])
                subprocess.call(['C:\\ProgramData\\Anaconda3\\Scripts\\telegram-send.exe', '---------shouldlong----------' + crypto.iloc[i]['Crypto'] + str(df.iloc[0]['Time'])])
                duration = 1000  # milliseconds
                freq = 440  # Hz
                winsound.Beep(freq, duration)
                    
        else:
            shouldLong = False
    
        #shouldShort() =>
        if float(df.iloc[0]['Low']) < float(crypto.iloc[i]['EMA223']) and crypto.iloc[i]['count_up'] >= min_durata_Up and (((crypto.iloc[i]['highest'] / float(df.iloc[0]['High']))-1)*100 ) > min_delta_Up:
               print('----------shouldShort-------------', crypto.iloc[i]['Crypto'], df.iloc[0]['Time'])
               subprocess.call(['C:\\ProgramData\\Anaconda3\\Scripts\\telegram-send.exe', '---------shouldShort----------' + crypto.iloc[i]['Crypto'] + str(df.iloc[0]['Time'])])
               duration = 1000  # milliseconds
               freq = 440  # Hz
               winsound.Beep(freq, duration)

        else:
           shouldShort = False
        
        
        if  float(df.iloc[0]['Low']) > float(crypto.iloc[i]['EMA223']):
            crypto.at[i, 'count_up'] = crypto.iloc[i]['count_up'] + 1
            if  crypto.iloc[i]['count_up'] == 1:
                
                #crypto.iloc[i]['min_close'] = float(df['Low'])
                crypto.at[i, 'highest'] = float(df.iloc[0]['High'])
        else:
            crypto.at[i, 'count_up'] = 0
            crypto.at[i, 'highest'] = 0
        crypto.at[i, 'highest'] = max(float(df.iloc[0]['High']) , crypto.iloc[i]['highest'])
        
        if float(df.iloc[0]['High']) <  float(crypto.iloc[i]['EMA223']):
            crypto.at[i, 'count_down']= crypto.iloc[i]['count_down'] + 1
            if crypto.iloc[i]['count_down'] == 1:
                
                #crypto.iloc[i]['max_close'] = float(df['High'])
                crypto.at[i, 'lowest'] = float(df.iloc[0]['Low'])
        else:
            crypto.at[i, 'count_down'] = 0
            crypto.at[i, 'lowest'] = 0
        crypto.at[i, 'lowest'] = min(float(df.iloc[0]['Low']), crypto.iloc[i]['lowest'])
    t1 = time.time()
    print(t1-t0)
    time.sleep(20)
