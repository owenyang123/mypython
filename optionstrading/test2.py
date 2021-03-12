# import basictools as bt
# import pymysql
# import pandas as pd
# import time
# con = pymysql.connect(host='localhost',
#                       user='owenyang',
#                       password='222121wj',
#                       db='stock',
#                       charset='utf8mb4',
#                       cursorclass=pymysql.cursors.DictCursor)
# frame = pd.read_sql("select * from stock.realdata where Date='2020-03-05'",con)
# print(frame)
from itertools import zip_longest
def maxp(*list1):
    res=0
    for i in zip_longest(*list1,fillvalue=float('-inf')):
        res+=max(i)
    return res
print(maxp([1,2,3],[2,4],[3,4,5]))
