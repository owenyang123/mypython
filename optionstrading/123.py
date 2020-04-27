import yfinance as yf
import numpy as np
aapl = yf.Ticker("AAPL")
#data=aapl.option_chain('2020-04-30').calls
print aapl.calendar.loc['Earnings Date'].tolist()[0]

print float(5/2)
str.is

#print data['ask']
