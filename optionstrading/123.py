import yfinance as yf
import numpy as np
import time
import datetime
import basictools as bt
import os
import seaborn as sns
import pandas as pd
import matplotlib as plt
data1=pd.read_csv('train.csv')
sns.factorplot('Sex',data=data1)

<<<<<<< HEAD
print bt.get_options_data("2020-05-07","call",*['ZM'])['ZM'].loc[lambda x:x['strike']== 130.0].loc[:,["ask","bid","strike"]]
=======
url="https://www.w3resource.com/pandas/dataframe/dataframe-loc.php"
>>>>>>> fef89eb78227e75d18c074e33d64d4c0dd1aa850
