import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import datetime
import os
import requests
import basictools as bt
import time
if __name__ == "__main__":
    maillist=[" owenyang@juniper.net"," pings@juniper.net"," hfzhang@juniper.net"]
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    content = pd.read_html(url)
    stocklist = content[0]['Symbol'].tolist()
    while(1):
        print('sp500 index data got')
        if not stocklist: exit()
        print("starting polling date from yahoo")
        earningdate = bt.get_next_event(*stocklist)
        print earningdate
        cur_date=str(datetime.date.today())
        msg=""
        print("finding the delta less then 20days")
        for i in earningdate:
            if bt.get_date_delta(earningdate[i],cur_date)<=20:
                msg+=i +" "+str(bt.get_date_delta(earningdate[i],cur_date))+" ,"
        if msg:bt.mail_notice(msg,*maillist)
        time.sleep(172800)




