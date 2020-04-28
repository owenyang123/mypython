import yfinance as yf
import numpy as np
aapl = yf.Ticker("AAPL")
<<<<<<< HEAD
data=aapl.option_chain('2020-04-30').calls
print data,data.index,data.columns
print data.loc[4:10,["bid","ask","strike","volume"]]
=======
#data=aapl.option_chain('2020-04-30').calls
print aapl.calendar.loc['Earnings Date'].tolist()[0]

print float(5/2)
str.is

#print data['ask']
>>>>>>> c422b1fa836541abd392b93d7c1bf37b2aec896a
