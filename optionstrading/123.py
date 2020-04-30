import yfinance as yf
import numpy as np
import time
import datetime
import basictools as bt
import os

temp = yf.Ticker("MSFT")
print str(temp.calendar.loc['Earnings Date'].tolist()[0])[0:10]
