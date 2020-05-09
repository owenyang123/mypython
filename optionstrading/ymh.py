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
import stockplay as sp
stocklist = ["TSLA","NTDOY"]
print sp.caifuziyou(stocklist)