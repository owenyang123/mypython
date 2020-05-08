import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp

url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()
print sp.wealthfree(stocklist)
'''
l= op.wealthfree(stocklist)
with open(r'ymh.csv','a') as fd:
    for t in l:
        writer=csv.writer(fd)
        writer.writerow([str(datetime.datetime.now())]+[bt.get_data(0)]+[bt.get_next_event(t[1])[t[1]]]+t)
'''


