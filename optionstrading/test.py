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
set1=set([])
for i in alllist:
    try:
        temp=yf.Ticker(i)
        set1.add(temp.info['sector'])
    except:pass

for i in set1:
    str1=i+".csv"
    with open(str1, 'a') as fd:
        writer = csv.writer(fd)
        writer.writerow([bt.get_data(0)])
