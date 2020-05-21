
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import time
import stockplay as sp
import csv
import yfinance as yf
sns.set(style="whitegrid")
if __name__ == "__main__":
    set1 = set(['Financial', 'Energy', 'Financial Services', 'Consumer Cyclical', 'Basic Materials', 'Communication Services','Industrials', 'Healthcare', 'Real Estate', 'Utilities', 'Technology', 'Consumer Defensive'])
    for i in set1:
        stocklist = []
        str1 = i + ".csv"
        with open(str1) as fd:
            for j in fd.readlines():
                temp = j.replace("\n", "")
                print i,temp

