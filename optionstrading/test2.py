import pandas as pd
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp
import yfinance as yf
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


#for i  in sp.caifuziyou(["UBER","AMT","VRSK","WM","SWKS","FANG","SYY","OKE","SYF","PEAK","ADBE"]):
#   print i

filename_tod=bt.get_data(0)+".csv"
filename_yes=bt.get_data(1)+".csv"
set_tod=set([])
set_yes=set([])
with open(filename_tod) as fd:
    for i in fd.readlines():
        if len(i) > 10:
            set_tod.add(i.replace("\n", "").split(",")[0])
with open(filename_yes) as fd:
    for i in fd.readlines():
        if len(i) > 10:
            set_yes.add(i.replace("\n", "").split(",")[0])
temp1=[]
print len(set_tod),len(set_yes)







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




