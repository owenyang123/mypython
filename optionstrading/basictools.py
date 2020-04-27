import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
def get_stock_data(start_time,end_time,*stocklist):
    if not stocklist:return {}
    data_dict={}
    for i  in stocklist:
        data1 = yf.download(i,start_time,end_time)
        data_dict[i]=data1
    return data_dict

def get_next_event(*stocklist):
    data_next_ear_data={}
    for i in stocklist:
        temp = yf.Ticker(i)
        data_next_ear_data[i]=temp.calendar.loc['Earnings Date'].tolist()[0]
    return data_next_ear_data[




if __name__ == "__main__":
    pass