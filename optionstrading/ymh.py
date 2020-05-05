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
if __name__ == "__main__":
    stocklist = ['JD','NIO','AMZN','UAL','OXY','T']
    while (1):
        with open('/var/www/html/ps.html', 'w') as file:
            file.write('<html> \n')
            file.write('    <head> \n')
            file.write('        <title>Stock Data</title> \n')
            file.write('    </head> \n')
            file.write('    <body> \n')
            for i in stocklist:
                file.write('        <H1> ' + i +" "+ bt.get_data(0)+' </H1> \n')
                file.write("        <img alt='no image1' src='" + i + "ps10days.png'></img> \n")
            file.write('    </body> \n')
            file.write('<html> \n')
        try:
            data1 = bt.get_stock_data(bt.get_data(95), bt.get_data(1), *stocklist)
            for i in data1:
                data1[i]["daily"] = data1[i]['Adj Close'].pct_change()
                days = 10
                dt = 1.0000 / days
                mu = data1[i]["daily"].mean()
                sigma = data1[i]["daily"].std()
                if data1[i]['Adj Close'].tolist() != []:
                    startprice = data1[i]['Adj Close'].tolist()[-1]
                else:
                    startprice = 0 - 100.00
                for j in range(100):
                    plt.plot(bt.perdict10days(startprice,mu,dt,sigma,days=10))
                str1="/var/www/html/"+i+"ps10days.png"
                print(str1)
                plt.savefig(str1)
                plt.clf()
                plt.cla()
                plt.close()
        except:
            plt.clf()
            plt.cla()
            plt.close()
            pass
        time.sleep(86400)