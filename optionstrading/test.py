import pymysql
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
con = pymysql.connect(host='localhost',
        user='owenyang',
        password='222121wj',
        db='stock',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
with con:
    with con.cursor() as cursor:
            cursor.execute("delete from stock.realdata")
            con.commit()
            cursor.execute("INSERT INTO stock.realdata SELECT  distinct Stocksymbol, Date, Prices FROM stock.stockdata")
            con.commit()


# frame = pd.read_sql("select * from stock.stockdata where Stocksymbol='SOXL'" ,con)
# frame.iloc[-200:].plot(subplots=False, figsize=(10, 4),x="Date",y='Prices')
# str1="testymh"+".png"
# plt.savefig(str1)

    




