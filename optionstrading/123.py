import yfinance as yf
import numpy as np
import time
import datetime
import basictools as bt
import pandas as pd
import os


while (1):
    aapl = yf.Ticker("MO")
    print (aapl.major_holders)
    print (aapl.calendar)
    print (sorted(aapl.options))
    print aapl.option_chain('2020-05-07').calls.loc[:,["ask","bid","strike"]]
    time.sleep(180)