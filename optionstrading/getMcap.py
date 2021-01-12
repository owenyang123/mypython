import yfinance as yf
import basictools as bt
import csv
stocklist=[]
set1=set([])
with open('nyselist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            stocklist.append(i.replace("\n", ""))
with open('nsdqlist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            stocklist.append(i.replace("\n", ""))
for i in stocklist:
    temp=yf.Ticker(i)
    try:
        if temp.info['marketCap']>=10000000000:
            set1.add(i)
            print i
    except:
        pass
with open("marketcap.csv", 'w') as fd:
    for t in set1:
        writer = csv.writer(fd)
        writer.writerow(t)



