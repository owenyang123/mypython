import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import time
import stockplay as sp
import csv
import yfinance as yf
import optionsplay as op
sns.set(style="whitegrid")
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()
l=sp.caifuziyou(stocklist)
filename_tod=bt.get_data(0)+".csv"
filename_yes=bt.get_data(1)+".csv"
set_tod=set([])
set_yes=set([])
with open(filename_tod, 'w') as fd:
    for t in l:
        if t[-1] != 0 :
            set_tod.add(t[0])
            writer = csv.writer(fd)
            writer.writerow(t)
with open(filename_yes) as fd:
    for i in fd.readlines():
        if len(i) > 10:
            set_yes.add(i.replace("\n", "").split(",")[0])
temp1=[]
for i in l:
    if i[0] not in set_yes and i[0] in set_tod:
        temp1.append([i[0],i[1],i[-1]])
temp1.sort(key=lambda x:x[-1])
print temp1




