import basictools as bt
import pymysql
import pandas as pd
import time
con = pymysql.connect(host='localhost',
                      user='owenyang',
                      password='222121wj',
                      db='stock',
                      charset='utf8mb4',
                      cursorclass=pymysql.cursors.DictCursor)
frame = pd.read_sql("select * from stock.realdata where Date='2020-03-05'",con)
print(frame)