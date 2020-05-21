import yfinance as yf
import pandas as pd
import csv
import basictools as bt
alllist = []
with open('nyselist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            alllist.append(i.replace("\n", ""))
with open('nsdqlist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            alllist.append(i.replace("\n", ""))
set1=set(['Financial','Energy','Financial Services','Consumer Cyclical','Basic Materials','Communication Services','Industrials','Healthcare','Real Estate','Utilities','Technology','Consumer Defensive'])
for i in alllist:
    try:
        temp=yf.Ticker(i)
        if temp.info['sector'] in set1 and temp.info['enterpriseValue']>1000000000:
            str1=temp.info['sector']+".csv"
            with open(str1, 'a') as fd:
                writer = csv.writer(fd)
                writer.writerow([i])
    except:pass


