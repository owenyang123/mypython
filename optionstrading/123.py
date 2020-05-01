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

url="https://www.w3resource.com/pandas/dataframe/dataframe-loc.php"