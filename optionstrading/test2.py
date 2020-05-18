import pandas as pd
import datetime
import basictools as bt
import time
import csv
import optionsplay as op
import stockplay as sp
'''
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = ['CSCO', 'NCLH', 'TTWO', 'VFC', 'ZBH', 'JWN', 'AEE', 'AAP', 'A', 'MAR', 'WMT', 'HRL', 'COTY', 'IFF', 'CPRT', 'LOW', 'ROST', 'SNPS', 'PGR', 'ADI', 'HPE', 'LB', 'UAA', 'AMCR', 'NLOK', 'KSS', 'BBY', 'NVDA', 'TJX', 'HD', 'MDT', 'MYL', 'INTU', 'AMAT', 'DXC']+['TQQQ']
l=sp.caifuziyou(stocklist)
l.sort(key=lambda x:x[2],reverse=True)
with open(r'stocks.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([str(datetime.datetime.now())]+t)
'''
print bt.get_data(0)
print bt.get_stock_data("2020-02-01","2020-05-16",*['NVDA'])