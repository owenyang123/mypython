import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
import optionsplay as op
import stockplay as sp
sns.set(style="whitegrid")
import stockplay as sp
str1='AMCR ,UAA ,RCL ,LIN ,KIM ,ZBH ,BR ,COTY ,MYL ,AMAT ,AEE ,MAR ,VFC ,IFF ,NLOK ,CSCO ,NCLH ,EXC'
stocklist = str1.replace(" ","").split(",")
print op.caifuziyou(stocklist)