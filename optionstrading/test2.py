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
import optionsplay as op
import csv

str1="LNT ,AMCR ,D ,ANSS ,ALB ,UAA ,LNC ,PWR ,CDW ,SBAC ,HII ,AES ,CTSH ,FRT ,ATO ,RCL ,EXR ,MET ,ES ,EOG ,AWK ,IRM ,SYY ,FISV ,FLT ,LIN ,CF ,MRO ,HPQ ,ESS ,DISH ,FTNT ,EQIX ,CVS ,KIM ,ZTS ,TMUS ,AEP ,J ,FOXA ,ED ,FIS ,BWA ,ZBH ,MAA ,BR ,COTY ,MYL ,AMAT ,AEE ,UDR ,DLR ,MAR ,FLIR ,QRVO ,AMP ,CTVA ,MCHP ,VFC ,DISCK ,NRG ,MTD ,CNP ,IFF ,NWSA ,NLOK ,CSCO ,GPN ,BLL ,ALXN ,REG ,WYNN ,VMC ,EVRG ,NCLH ,GPC ,BKNG ,EXC ,BDX ,APA ,PYPL"
stocklist=str1.replace(" ","").split(",")
l=[['put', 'AEP', '2020-08-20', 1.0, "nan", 0.25, 45.0, "nan"],
['put', 'EXC', '2020-05-14', 0.9359999999999999, 0.25381816517223, 1.1, 34.0, 0.6838509863288453],
['put', 'CSCO', '2020-05-21', 0.9359999999999999, 0.1121622034021327, 1.48, 41.0, 0.365397800161412],
['put', 'LIN', '2020-05-14', 0.9333333333333333, 0.3133944730146215, 5.45, 180.0, 0.7206088840940629],
['put', 'LNT', '2020-05-14', 0.9413333333333334, 0.9439999229029604, 0.9500000000000001, 45.0, 0.8791864356023922],
['call', 'D', '2020-05-14', 0.6106666666666667, 0.6582400716145834, 1.875, 77.5, 0.01919047109208589],
['put', 'ED', '2020-05-14', 0.9306666666666666, 0.2935651696246605, 2.3, 75.0, 0.694489693008723],
['call', 'DLR', '2020-05-14', 0.7653333333333333, 0.7874626501282649, 3.35, 150.0, 0.4673297815097094],
['put', 'MTD', '2020-05-14', 0.9333333333333333, 0.14492802734375004, 25.0, 720.0, 0.47333489211711466],
['put', 'PWR', '2020-05-14', 0.9333333333333333, 0.1543829735289228, 1.175, 34.0, 0.5015067844414183],
['put', 'BLL', '2020-05-14', 0.9093333333333333, 0.4020266927083334, 1.875, 65.0, 0.6838093362676845]]

with open(r'document.csv','a') as fd:
    for t in l:
        writer=csv.writer(fd)
        writer.writerow([bt.get_data(0)]+t)




