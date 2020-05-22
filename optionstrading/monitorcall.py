import datetime
import basictools as bt
import time
import stockplay as sp
import optionsplay as op
import pandas as pd
import csv
if __name__ == "__main__":
    maillist = [" owenyang@juniper.net", " pings@juniper.net", " hfzhang@juniper.net", "xinzhou@juniper.net"]
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    content = pd.read_html(url)
    stocklist = content[0]['Symbol'].tolist()
    print('sp500 index data got')
    cur_date = str(datetime.date.today())
    if not stocklist: exit()
    print("starting polling date from yahoo")
    earningdate = bt.get_next_event(*stocklist)
    msg=""
    print("finding the delta less then 10days")
    for i in earningdate:
        if 0<bt.get_date_delta(earningdate[i],cur_date)<=10:
            msg+=i+","
    str1 = "caifu"+bt.get_data(0)+".csv"
    list1=msg[:-1].split(",")
    print list1
    l=sp.caifuziyou(list1)
    with open(str1, 'a') as fd:
        for t in l:
            if t[-1] != 0:
                writer = csv.writer(fd)
                writer.writerow(t)
    l = op.caifuziyou(list1)
    with open(str1, 'a') as fd:
        for t in l:
            if t[-1] != 0:
                writer = csv.writer(fd)
                writer.writerow(t)

    #if msg:bt.mail_notice("Todays Briefing from SP500",maillist)