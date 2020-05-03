import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import matplotlib.dates as dates
# Get the data for the stock Apple by specifying the stock ticker, start date, and end date
data1 = yf.download('AAPL','2020-01-13','2020-04-20')
data2 = yf.download('AMZN','2020-01-13','2020-04-20')
x1=np.array(data1.index)
y=np.array([i for i in data1['Close']])
x2=np.array(data2.index)
z=np.array([i for i in data2['Close']])
fig,axes=plt.subplots(1,2,figsize=(10,5))
axes[0].plot_date(x1,y,"-")
axes[0].plot_date(x1,y*1.5,"-")
axes[0].yaxis.grid(True)
axes[1].plot_date(x2,z,"-")
fig.autofmt_xdate()
xtr1="12331.png"
plt.savefig(xtr1)



