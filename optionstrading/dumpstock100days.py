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
if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    content = pd.read_html(url)
    stocklist = content[0]['Symbol'].tolist()
    with open('/var/www/html/1.html', 'w') as file:
        file.write('<html> \n')
        file.write('    <head> \n')
        file.write('        <title>Stock Data</title> \n')
        file.write('    </head> \n')
        file.write('    <body> \n')
        for i in stocklist:
            file.write('        <H1> ' + i +" "+bt.get_data(0)+ ' </H1> \n')
            file.write("        <img alt='no image1' src='" + i + ".png'></img> \n")
        file.write('    </body> \n')
        file.write('<html> \n')
    while(1):
        data1 = bt.get_stock_data(bt.get_data(100), bt.get_data(0), *stocklist)
        for i in sorted(stocklist):
            try:
                data1[i].plot(subplots=False, figsize=(10, 4))
                str1="/var/www/html/"+i+".png"
                plt.savefig(str1)
                plt.clf()
                plt.cla()
                plt.close()
            except:
                plt.clf()
                plt.cla()
                plt.close()
        time.sleep(86400)

