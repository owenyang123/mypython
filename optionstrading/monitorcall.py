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
    print('sp500 index gotten')
    while(1):
        if not stocklist:exit()
        print("starting poll date from yahoo")
        earningdate=bt.get_next_event(*stocklist)
        cur_date=str(datetime.date.today())
        msg=""
        print("finding the delta less then 20days")
        for i in earningdate:
            if bt.get_date_delta(earningdate[i][0:10],cur_date)<=20:
                msg+=i +" "+str(bt.get_date_delta(earningdate[i][0:10],cur_date))+"  ,"
        bt.mail_notice(msg,*maillist)
        time.sleep(172800)




