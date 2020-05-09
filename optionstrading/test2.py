import pandas as pd
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp
str1="VNQ"
stocklist=str1.replace(" ","").split(",")
l=sp.caifuziyou(stocklist)
with open(r'ymh.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([str(datetime.datetime.now())]+t)
l=op.caifuziyou(stocklist)
with open(r'ymh.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([str(datetime.datetime.now())]+t)
