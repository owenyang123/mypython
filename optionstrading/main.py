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

def caifuziyou(stocklist):
    days0to15_data = bt.get_stock_data(bt.get_data(20), bt.get_data(0), *stocklist)
    days0to180_data = bt.get_stock_data(bt.get_data(180), bt.get_data(30), *stocklist)
    kelly_data={}
    for i in days0to15_data:
        try:
            x1=days0to15_data[i]['Adj Close'].tolist()[-1]
            x2=max(days0to180_data[i]['Adj Close'].tolist())
            if x2/x1 >=2:kelly_data[i]=x1/x2
        except:
            pass

    return kelly_data

if __name__ == "__main__":
    stocklist = []
    with open('nyselist') as f:
        for i in f.readlines():
            stocklist.append(i.replace("\n", ""))
    l=caifuziyou(stocklist)
    for i in l:
        print i,l[i]


