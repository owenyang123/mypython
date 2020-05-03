import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
sns.set(style="whitegrid")


x=bt.get_stock_data("2019-04-01","2020-05-01",*["LMT"])
print x

#x[["Adj Close","10 days","30 days","50 days"]].plot(subplots=False,figsize=(10,4))

newdata=pdr.DataReader(['OXY'],'yahoo',"2019-04-01","2020-05-03")
