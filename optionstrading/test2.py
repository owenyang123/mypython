import pandas as pd
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp
nyse=[]
nsdq=[]
with open('nyselist') as f:
    for i in f.readlines():
        nyse.append(i.replace("\n",""))
l=sp.caifuziyou(nyse)
with open(r'ymh.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([bt.get_data(0)]+t)

with open('nsdqlist') as f:
    for i in f.readlines():
        nsdq.append(i.replace("\n",""))

l=sp.caifuziyou(nsdq)
with open(r'ymh.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([bt.get_data(0)]+t)

