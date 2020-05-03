import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
sns.set(style="whitegrid")


x=bt.get_stock_data("2019-04-01","2020-05-01",*["LMT"])['LMT']
days=[10,30,50]
for day in days:
    columnday=str(day)+" days"
    x[columnday]=x['Adj Close'].rolling(day).mean()
x[["Adj Close","10 days","30 days","50 days"]].plot(subplots=False,figsize=(10,4))

newdata=pdr.DataReader(['OXY'],'yahoo',"2019-04-01","2020-05-03")

print  x[["Adj Close","10 days","30 days","50 days"]]
plt.show()