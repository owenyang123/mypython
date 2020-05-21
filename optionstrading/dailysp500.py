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
str1="JWN ,NTAP  ,COST  ,KEYS  ,ADSK  ,PVH  ,DG  ,ULTA  ,DLTR  ,HPQ  ,AZO  ,DXC"
stocklist=str1.replace(" ","").split(",")
l=sp.caifuziyou(stocklist)
with open(r'today.csv', 'a') as fd:
    for t in l:
        if t[-1] != 0:
            writer = csv.writer(fd)
            writer.writerow(t)
l=op.caifuziyou(stocklist)
with open(r'today.csv', 'a') as fd:
    for t in l:
        if t[-1] != 0:
            writer = csv.writer(fd)
            writer.writerow(t)
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()
l=sp.caifuziyou(stocklist)
with open(r'today.csv', 'a') as fd:
    for t in l:
        if t[-1] != 0:
            writer = csv.writer(fd)
            writer.writerow(t)

