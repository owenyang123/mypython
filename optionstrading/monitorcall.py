import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import datetime
import basictools as bt
import time
if __name__ == "__main__":
    maillist=[" owenyang@juniper.net"," pings@juniper.net"," hfzhang@juniper.net","xinzhou@juniper.net"]
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    content = pd.read_html(url)
    stocklist = content[0]['Symbol'].tolist()
    while(1):
        try:
            print('sp500 index data got')
            if not stocklist: exit()
            print("starting polling date from yahoo")
            earningdate = bt.get_next_event(*stocklist)
            print earningdate
            if not earningdate:print "1231"
            cur_date=str(datetime.date.today())
            msg=""
            print("finding the delta less then 10days")
            for i in earningdate:
                if 0<bt.get_date_delta(earningdate[i],cur_date)<=10:
                    msg+=i +" "+" ,"
            #if msg:bt.mail_notice(msg[:-1],*maillist)
            print msg[:-1]
            time.sleep(40000)
        except:
            print ("error seen")
            pass




