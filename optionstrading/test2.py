'''

while(1):
    try:
        x=bt.get_options_data("2020-09-17","call",*["OXY"])
        print(x["OXY"][["strike","bid","ask","volume","openInterest"]].loc[lambda df: df['strike'] == 15.0])
        x=bt.get_options_data("2020-05-07","call",*["ATVI"])
        print(x["ATVI"][["strike","bid","ask","volume","openInterest"]].loc[lambda df: df['strike'] == 66.0])
        time.sleep(120)
    except:
        time.sleep(60)
        pass


import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
sns.set(style="whitegrid")
data1 = bt.get_stock_data(bt.get_data(95), bt.get_data(1), *['OXY','T','MMM'])
for i in data1:
    data1[i]["daily"] = data1[i]['Adj Close'].pct_change()
    days = 10
    dt = 1.0000 / days
    mu = data1[i]["daily"].mean()
    sigma = data1[i]["daily"].std()
    startprice = data1[i]['Adj Close'].tolist()[-1]
    for j in xrange(100):
        plt.plot(bt.perdict10days(startprice,mu,dt,sigma,days=10))
    print "draw done"
    str1="/var/www/html/"+i+"10days.png"
    print(str1)
    plt.savefig(str1)
    plt.clf()
    plt.cla()
    plt.close()

'''
import basictools as bt

print bt.kelly_caculation(0.784, 0.4454479006901841)