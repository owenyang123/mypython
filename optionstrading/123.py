import yfinance as yf
import numpy as np
import time
import datetime
import basictools as bt
import os

print bt.get_options_data("2020-05-07","call",*['ZM'])['ZM'].loc[lambda x:x['strike']== 130.0].loc[:,["ask","bid","strike"]]
