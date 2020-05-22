import pandas as pd
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp
import yfinance as yf
import yahoofinancials as yf1
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()

assets = stocklist
print yf.download('FB', '2019-12-01', '2019-12-30')

'''
nyse=[]
nsdq=[]
with open('nyselist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            nyse.append(i.replace("\n",""))
with open('nsdqlist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            nsdq.append(i.replace("\n",""))

len1=len(nyse)/100+1
for i in range(len1):
    l=sp.caifuziyou(nyse[i*100:i*100+100])
    with open(r'ymh.csv', 'a') as fd:
        for t in l:
            if t[-1] != 0:
                writer = csv.writer(fd)
                writer.writerow([bt.get_data(0)] + t)

len1=len(nsdq)/100+1
for i in range(len1):
    l=sp.caifuziyou(nsdq[i*100:i*100+100])
    with open(r'ymh.csv', 'a') as fd:
        for t in l:
            if t[-1] != 0:
                writer = csv.writer(fd)
                writer.writerow([bt.get_data(0)] + t)
'''




