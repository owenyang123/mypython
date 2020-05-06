import numpy as np
import csv
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
sns.set(style="whitegrid")

str1="LNT ,AMCR ,D ,APA ,PYPL,EVRG "
stocklist=str1.replace(" ","").split(",")
earningdate = bt.get_next_event(*stocklist)
latest_option_date={}
optiondata_call={}
optiondata_put={}
for i in earningdate:
    temp=yf.Ticker(i)
    for j in sorted(temp.options):
        if 3<bt.get_date_delta(j,earningdate[i])<35:
            latest_option_date[i]=j
            break
    if i in latest_option_date:
        optiondata_call[i] = temp.option_chain(latest_option_date[i]).calls
        optiondata_put[i] = temp.option_chain(latest_option_date[i]).puts

'''
check the stock flipping  more than 2%
'''
days0to100_data = bt.get_stock_data(bt.get_data(100), bt.get_data(0), *stocklist)
days0to5_data = bt.get_stock_data(bt.get_data(5), bt.get_data(0), *stocklist)
days0to30_data = bt.get_stock_data(bt.get_data(30), bt.get_data(0), *stocklist)
days30to60_data = bt.get_stock_data(bt.get_data(60), bt.get_data(30), *stocklist)
days60to90_data = bt.get_stock_data(bt.get_data(90), bt.get_data(60), *stocklist)
kelly_data={}
probability_rate=np.array([0.5,1.0,0.25,0.125])
for i in latest_option_date:
    '''
    get p
    '''
    days0to100_data[i]["daily"] = days0to100_data[i]['Adj Close'].pct_change()
    days = 10
    dt = 1.0000 / days
    mu = days0to100_data[i]["daily"].mean()
    sigma = days0to100_data[i]["daily"].std()
    startprice = days0to100_data[i]['Adj Close'].tolist()[-1]
    temp1,temp2,temp3,temp4=0.0,0.0,0.0,0.0
    for j in range(100):
        pricelist=bt.perdict10days(startprice, mu, dt, sigma, days=10)
        if bt.incornot(list(pricelist))>0.02:temp1+=1
    temp1=float(temp1)/100
    if bt.incornot(days0to30_data[i]['Adj Close'].tolist())>0:temp2=1
    if bt.incornot(days30to60_data[i]['Adj Close'].tolist()) > 0: temp3 = 1
    if bt.incornot(days60to90_data[i]['Adj Close'].tolist()) > 0: temp4 = 1
    p=sum(probability_rate*np.array([temp1,temp2,temp3,temp4]))/sum(probability_rate)
    corp=""
    if p>=0.7:corp="call"
    elif p<=0.2:corp="put"
    else:corp="hold"
    if corp=="call":kelly_data[i]=[corp,i,latest_option_date[i],p]
    elif corp=="put":kelly_data[i]=[corp,i,latest_option_date[i],1-p]
    else:kelly_data[i]=[corp,i,-1,-1]
    '''
    get b
    '''
    strikelist_call=optiondata_call[i]["strike"].tolist()
    strikelist_put = optiondata_put[i]["strike"].tolist()
    target=bt.closestprice(strikelist_call,startprice)
    option_call_price=float(optiondata_call[i].loc[lambda df: df['strike'] == target][["bid","ask"]].sum(axis=1).tolist()[0]/2)
    option_put_price = float(optiondata_put[i].loc[lambda df: df['strike'] == target][["bid", "ask"]].sum(axis=1).tolist()[
        0]/2)
    b_call=((startprice*0.04-option_call_price)/option_call_price)
    b_put=((startprice*0.04-option_put_price)/option_put_price)
    if kelly_data[i][0]=="call":kelly_data[i].append(b_call)
    if kelly_data[i][0] == "put": kelly_data[i].append(b_put)

for i in kelly_data:
    if kelly_data[i][0]!="hold":
        print kelly_data[i][3],kelly_data[i][4]
print bt.kelly_caculation(0.9093333333333333,0.273111131456)
