import pandas as pd
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp
str1="AMCR ,UAA ,RCL ,LIN ,KIM ,ZBH ,BR ,COTY ,MYL ,AMAT ,AEE ,MAR ,VFC ,IFF ,NLOK ,CSCO ,NCLH ,EXC"
stocklist=str1.replace(" ","").split(",")
l=sp.caifuziyou(stocklist)
with open(r'ymh.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([str(datetime.datetime.now())]+t)

