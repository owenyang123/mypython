import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import time
import stockplay as sp
import csv
import yfinance as yf
sns.set(style="whitegrid")
if __name__ == "__main__":
    alllist=[]
    with open('nyselist') as f:
        for i in f.readlines():
            if "-" not in i and "." not in i:
                alllist.append(i.replace("\n", ""))
    with open('nsdqlist') as f:
        for i in f.readlines():
            if "-" not in i and "." not in i:
                alllist.append(i.replace("\n", ""))
    alllist.sort()
    for i in alllist:
        if i.isalpha():
            try:
                temp = yf.Ticker(i)
                if temp.info and temp.info['enterpriseValue']>10000000000:
                    l=sp.caifuziyou([i])
                    with open(r'ymh.csv', 'a') as fd:
                        for t in l:
                            if t[-1] != 0 and t[-3]>0.9:
                                writer = csv.writer(fd)
                                writer.writerow([bt.get_data(0)] + t+[temp.info['enterpriseValue']])
            except:pass
