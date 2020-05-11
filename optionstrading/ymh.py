import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
import optionsplay as op
import stockplay as sp
sns.set(style="whitegrid")
import stockplay as sp

'''
str1='COST,TQQQ'
stocklist = str1.replace(" ","").split(",")
print op.caifuziyou(stocklist)

print sp.caifuziyou(stocklist)
'''

def rmvdate(str1):
    if not str1:return []
    list1=str1.replace(" ","").split(",")
    temp=[]
    for i in list1:
        for j in range(len(i)):
            if i[j]=="2":
                temp.append((i[0:j],i[j:]))
                break
    return temp


str1='CSCO2020-05-13 ,NCLH2020-05-14 ,TTWO2020-05-20 ,VFC2020-05-15 ,ZBH2020-05-11 ,JWN2020-05-19 ,AEE2020-05-11 ,AAP2020-05-19 ,A2020-05-21 ,MAR2020-05-11 ,WMT2020-05-19 ,HRL2020-05-21 ,COTY2020-05-11 ,IFF2020-05-11 ,CPRT2020-05-20 ,LOW2020-05-20 ,ROST2020-05-21 ,SNPS2020-05-20 ,PGR2020-05-20 ,ADI2020-05-20 ,HPE2020-05-21 ,LB2020-05-20 ,UAA2020-05-11 ,AMCR2020-05-11 ,NLOK2020-05-14 ,KSS2020-05-19 ,BBY2020-05-21 ,NVDA2020-05-21 ,TJX2020-05-21 ,HD2020-05-19 ,MDT2020-05-21 ,MYL2020-05-11 ,INTU2020-05-21 ,AMAT2020-05-14 ,DXC2020-05-21 '

url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()

print sp.caifuziyou(stocklist)