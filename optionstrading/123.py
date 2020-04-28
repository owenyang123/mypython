import yfinance as yf
import numpy as np
aapl = yf.Ticker("AAPL")

data=aapl.option_chain('2020-04-30').calls
print data,data.index,data.columns
print data.loc[4:10,["bid","ask","strike","volume"]]

