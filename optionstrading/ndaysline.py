import basictools as bt
import pymysql
import pandas as pd
import time
import matplotlib.pyplot as plt
con = pymysql.connect(host='localhost',
                      user='owenyang',
                      password='222121wj',
                      db='stock',
                      charset='utf8mb4',
                      cursorclass=pymysql.cursors.DictCursor)
frame = pd.read_sql("select * from stock.realdata where Stocksymbol='AMD'",con).set_index('Date')
frame.index = pd.to_datetime(frame.index)
list1=[]
for ind in frame.index:
    list1.append([ind,frame['Prices'][ind]])
dict1,sum={},0
for i in range(len(list1)):
    sum+=list1[i][1]
    if i>=50:
        sum-=list1[i-50][1]
        dict1[list1[i][0]]=sum/50.00
frame2=pd.DataFrame.from_dict(dict1,orient='Index', columns=['Prices'])
x=pd.concat([frame, frame2], axis=1)
x.plot(subplots=False, figsize=(10, 4))
plt.show()


