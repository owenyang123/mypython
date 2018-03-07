# coding="utf-8"
import numpy as np
import MySQLdb
import sqlfun
import datetime
from matplotlib.pyplot import plot
from matplotlib.pyplot import show

conn=MySQLdb.connect(host='localhost',user="root",passwd="222121wj",db="stock",charset="utf8")
cursor = conn.cursor()
x='*'
y='goog'
z=' ORDER by date'
tmp=sqlfun.select(x,y,z)
price=[]
volume=[]
price_mon=[]
price_tue=[]
price_wed=[]
price_thu=[]
price_fri=[]
volume_mon=[]
volume_tue=[]
volume_wed=[]
volume_thu=[]
volume_fri=[]
for i in tmp:
    x1=str(i[0])
    weeks=datetime.datetime.strptime(x1, "%Y-%m-%d").date().weekday()
    k=float(i[1])
    price.append(k)
    m=float(i[2])
    volume.append(m)
    if weeks==0:
       price_mon.append(k)
       volume_mon.append(m)
    elif weeks==1:
       price_tue.append(k)
       volume_tue.append(m)
    elif weeks==2:
       price_wed.append(k)
       volume_wed.append(m)
    elif weeks==3:
       price_thu.append(k)
       volume_thu.append(m)
    elif weeks==4:
       price_fri.append(k)
       volume_fri.append(m)
    else:
        print "really"
sum0=float(0)
sum1=float(0)
for q in range(len(price)):
    sum0=sum0+price[q]*volume[q]
    sum1=sum1+volume[q]
print sum0/sum1
sum0=float(0)
sum1=float(0)
for q in range(len(price_mon)):
    sum0=sum0+price_mon[q]*volume_mon[q]
    sum1=sum1+volume_mon[q]
print sum0/sum1
sum0=float(0)
sum1=float(0)
for q in range(len(price_tue)):
    sum0=sum0+price_tue[q]*volume_tue[q]
    sum1=sum1+volume_tue[q]
print sum0/sum1
sum0=float(0)
sum1=float(0)
for q in range(len(price_wed)):
   sum0=sum0+price_wed[q]*volume_wed[q]
   sum1=sum1+volume_wed[q]
print sum0/sum1
sum0=float(0)
sum1=float(0)
for q in range(len(price_thu)):
    sum0=sum0+price_thu[q]*volume_thu[q]
    sum1=sum1+volume_thu[q]
print sum0/sum1
sum0=float(0)
sum1=float(0)
for q in range(len(price_fri)):
    sum0=sum0+price_fri[q]*volume_fri[q]
    sum1=sum1+volume_fri[q]
print sum0/sum1
log_volatility=np.diff(np.log(price))
volatility_2year=(np.std(log_volatility)/np.mean(log_volatility))/np.sqrt(1./252.)
print volatility_2year
print volatility_2year*np.sqrt(1./12.)
kday=int(raw_input('please input days:'))
kday1=str(kday+1)
x='*'
y=''
z=' (select * from goog limit '+ kday1+' ) as a ORDER by a.date  '
h=[]
l=[]
previous=[]
tmp=sqlfun.select(x,y,z)
print tmp
days=len(tmp)
truerange=np.array
for i in range(1,days):
    previous.append(tmp[i-1][1])
    h.append(tmp[i][4])
    l.append(tmp[i][5])
h=np.array(h)
l=np.array(l)
previous=np.array(previous)
truerange=np.maximum(h - l, h - previous, previous - l)
atr = np.zeros(kday)
atr[0] = np.mean(truerange)
for i in range(1, kday):
    atr[i] = (kday - 1) * atr[i - 1] + truerange[i]
    atr[i] /= kday
print "ATR\n", atr
print 100*atr/h
print np.mean(100*atr/h)
print h
weights = np.exp(np.linspace(-1. , 0. , 5))
weights /= weights.sum()
ema = np.convolve(weights, h)[4:-4]
print ema
print len(ema)
print len(atr)
print h[4:-4]
t = np.arange(4, len(h))
plot(t, h[4:], lw=2.0)
plot(t, ema, lw=4.0)
show()
cursor.close()
conn.close()
print price
t=np.array(price)
c=t[-10:]
c=c[::-1]
print np.array(c)

A = np.zeros((10,10), float)
print A

for i in range(10):
    A[i, ] = t[-10 - 1 - i: - 1 - i]
print "A", A

(x, residuals, rank, s) = np.linalg.lstsq(A, np.array(c))

print x, residuals, rank, s

print np.dot(c, x)