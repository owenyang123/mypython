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
            set_yes.add(i.replace("\n", "").split(",")[1])
for i in set_tod:
    if i not in set_yes:
        print i





