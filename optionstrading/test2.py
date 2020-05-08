import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import datetime
import basictools as bt
import time
import csv
import optionsplay as op

str1="LNT ,AMCR ,UAA ,PWR ,HII ,AES ,CTSH ,RCL ,EOG ,IRM ,FISV ,FLT ,LIN ,DISH ,KIM ,ED ,FIS ,ZBH ,BR ,COTY ,MYL ,AMAT ,A"

stocklist=str1.replace(" ","").split(",")

l= op.wealthfree(stocklist)


with open(r'document.csv','a') as fd:
    for t in l:
        writer=csv.writer(fd)
        writer.writerow([bt.get_data(0)]+[bt.get_next_event(t[1])[t[1]]]+t)