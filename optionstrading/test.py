import yfinance as yf
import pandas as pd
import csv
import basictools as bt
import stockplay as sp
import optionsplay as op
alllist = []
'''
with open('nyselist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            alllist.append(i.replace("\n", ""))
with open('nsdqlist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            alllist.append(i.replace("\n", ""))
set1=set(['Financial','Energy','Financial Services','Consumer Cyclical','Basic Materials','Communication Services','Industrials','Healthcare','Real Estate','Utilities','Technology','Consumer Defensive'])
for i in set1:
    stocklist=[]
    str1=i+".csv"
    str2=bt.get_data(0)+str1
    with open(str1) as fd:
        for line in fd.readlines():
            temp=line.replace("\n","")
            if temp and temp!="":stocklist.append(temp)
    l=sp.caifuziyou(stocklist)
    with open(str2, 'a') as fd:
        for t in l:
            if t[-1] != 0:
                writer = csv.writer(fd)
                writer.writerow([i]+ t)
    l=op.caifuziyou(stocklist)
    with open(str2, 'a') as fd:
        for t in l:
            if t[-1] != 0:
                writer = csv.writer(fd)
                writer.writerow([i]+ t)


'''

l=[1,2,3,4,5]
print filter(lambda x:x>2,l)