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
<<<<<<< HEAD
from futu
=======
<<<<<<< HEAD
import fu
print sp.caifuziyou(['MELI'])

=======
import random

while (1):
    print random.choice('|| _')
>>>>>>> b9f24b941fcb732c184f80757afc2f774cffd276

>>>>>>> 3c36a687fe047e535c5a8ad29196dbf3c65b9296



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




