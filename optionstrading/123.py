import yfinance as yf
import numpy as np
<<<<<<< HEAD
#aapl = yf.Ticker("AAPL")
#data=aapl.option_chain('2020-04-30').calls
#print aapl.calendar.loc['Earnings Date'].tolist()[0]
#print float(5/2)
import time
import datetime

x=datetime.date.today()
y=datetime.timedelta(days=100)
print x-y
=======
aapl = yf.Ticker("AAPL")

data=aapl.option_chain('2020-04-30').calls
print data,data.index,data.columns
print data.loc[4:10,["bid","ask","strike","volume"]]

>>>>>>> 5fb773629f0574a3e74f6be0cc3b740df59f129f
