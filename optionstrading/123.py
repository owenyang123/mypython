import yfinance as yf
import numpy as np
import time
import datetime

aapl = yf.Ticker("MSFT")
print aapl.calendar
print sorted(aapl.options)
print aapl.option_chain('2020-04-30').calls.loc[:,["bid","strike"]]
