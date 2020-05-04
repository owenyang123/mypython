import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
sns.set(style="whitegrid")

'''
sns.set(style="whitegrid")
x=bt.get_stock_data("2019-04-01","2020-05-01",*["LMT"])
print x
x['LMT'].plot(subplots=False,figsize=(10,4))
newdata=pdr.DataReader(['OXY'],'yahoo',"2019-04-01","2020-05-03")
plt.show()
xx1=plt
xx2=plt
data1 = yf.download('AAPL','2020-01-13','2020-04-20')
data2 = yf.download('AMZN','2020-01-13','2020-04-20')
x1=np.array(data1.index)
y=np.array([i for i in data1['Close']])
x2=np.array(data2.index)
z=np.array([i for i in data2['Close']])

xx1.plot_date(x1,y,"-")
xx1.savefig('test1.png')

xx2.plot_date(x2,z,"-")
xx2.savefig('test2.png')

stocklist=['AAPL','OXY']
with open('1.html', 'w') as file:
    file.write('<html> \n')
    file.write('    <head> \n')
    file.write('        <title>Stock Data</title> \n')
    file.write('    </head> \n')
    file.write('    <body> \n')
    for i in stocklist:
        file.write('        <H1>'+i+'</H1> \n')
        file.write("        <img alt='no image1' src='"+i+".png'></img> \n")
    file.write('    </body> \n')
    file.write('<html> \n')
<<<<<<< HEAD
    x=bt.get_stock_data("2019-04-01","2020-05-01",*["LMT"])
x['LMT'].plot(subplots=False,figsize=(10,4))
plt.show()


l=["7asdb","6bca"]
l.sort()
print l

    
sns.distplot(x["daily"].dropna(),bins=100,color='purple')
plt.show()
print x["daily"].quantile(1)
'''

sns.set(style="whitegrid")
x=yf.download("XOM","2020-02-01","2020-05-04")
x["daily"]=x['Close'].pct_change()

print x['Close'].tolist()[-1]

days=10
dt=1.0000/days
mu=x["daily"].mean()
sigma=x["daily"].std()
startprice=43
def mc(startprice,days,mu,dt,sigma):
    price=np.zeros(days)
    price[0]=startprice
    shock=np.zeros(days)
    drift=np.zeros(days)
    for x in xrange(1,days):
        shock[x]=np.random.normal(loc=mu*dt,scale=sigma*np.sqrt(dt))
        drift[x]=mu*dt
        price[x]=price[x-1]+(price[x-1]*(drift[x]+shock[x]))
    return price


for run in xrange(100):
    plt.plot(mc(startprice,days,mu,dt,sigma))
plt.show()


import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
sns.set(style="whitegrid")
if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    content = pd.read_html(url)
    stocklist = content[0]['Symbol'].tolist()
    with open('/var/www/html/2.html', 'w') as file:
        file.write('<html> \n')
        file.write('    <head> \n')
        file.write('        <title>Stock Data</title> \n')
        file.write('    </head> \n')
        file.write('    <body> \n')
        for i in stocklist:
            file.write('        <H1> ' + i + ' </H1> \n')
            file.write("        <img alt='no image1' src='" + i + "10days.png'></img> \n")
        file.write('    </body> \n')
        file.write('<html> \n')
    while(1):
        data1 = bt.get_stock_data(bt.get_data(95), bt.get_data(1), *stocklist)
        for i in data1:
            data1[i]["daily"] = data1[i]['Adj Close'].pct_change()
            days = 10
            dt = 1.0000 / days
            mu = data1[i]["daily"].mean()
            sigma = data1[i]["daily"].std()
            if data1[i]['Adj Close'].tolist()!=[]:
                startprice = data1[i]['Adj Close'].tolist()[-1]
            else:
                startprice=0-100.00
            for j in range(100):
                plt.plot(bt.perdict10days(startprice,mu,dt,sigma,days=10))
            str1="/var/www/html/"+i+"10days.png"
            print(str1)
            plt.savefig(str1)
            plt.clf()
            plt.cla()
            plt.close()
        time.sleep(3600*24)