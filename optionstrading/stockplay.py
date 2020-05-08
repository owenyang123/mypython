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

def wealthfree(stocklist):
    days0to100_data = bt.get_stock_data(bt.get_data(100), bt.get_data(0), *stocklist)
    days0to5_data = bt.get_stock_data(bt.get_data(5), bt.get_data(0), *stocklist)
    days0to10_data = bt.get_stock_data(bt.get_data(10), bt.get_data(0), *stocklist)
    days0to30_data = bt.get_stock_data(bt.get_data(30), bt.get_data(0), *stocklist)
    kelly_data={}
    probability_rate=np.array([0.3,0.5,0.8,1.0])
    for i in stocklist:
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
        bsum=0
        for j in range(100):
            pricelist=bt.perdict10days(startprice, mu, dt, sigma, days=10)
            if bt.incornot(list(pricelist))>0.05:
                temp1+=1
                bsum+=bt.incornot(list(pricelist))
        b=bsum/temp1
        temp1=float(temp1)/100
        if bt.incornot(days0to5_data[i]['Adj Close'].tolist())>0.03:temp2=1
        if bt.incornot(days0to10_data[i]['Adj Close'].tolist()) > 0.05: temp3 = 1
        if bt.incornot(days0to30_data[i]['Adj Close'].tolist()) > 0.1: temp4 = 1
        p=sum(probability_rate*np.array([temp1,temp2,temp3,temp4]))/sum(probability_rate)
        kelly_data[i]=[i,p,b]
    l = []
    print kelly_data
    for i in kelly_data:
        kelly_data[i]=bt.kelly_caculation(kelly_data[i][-2],kelly_data[i][-1])
        l.append([i,kelly_data[i]])
    return l

if __name__ == "__main__":
    pass

