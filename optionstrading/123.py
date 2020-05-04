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
'''

l=["7asdb","6bca"]
l.sort()
print l
=======
    
sns.distplot(x["daily"].dropna(),bins=100,color='purple')
plt.show()
print x["daily"].quantile(1)
'''

sns.set(style="whitegrid")
x=yf.download("XOM","2020-02-01","2020-05-01")
x["daily"]=x['Close'].shift(1)/x['Close']-1.0
print x

days=60
dt=1.0000/days
mu=x["daily"].mean()
sigma=x["daily"].std()
print mu
print sigma
startprice=59
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
>>>>>>> 1f9159558a23ee29581ac7b1696e0252494d5db2

