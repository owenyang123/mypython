import basictools as bt
import pymysql
import pandas as pd

url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist() + ['pdd', "sqqq", "tqqq", "pltr", "qqq", "vldr", "SOXL"]
capset = set()
with open('gt10blist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            capset.add(i.replace("\n", ""))
stocklist += list(capset)
stocklist = list(set(stocklist))
cur_date=bt.get_data(0)
yes_date=bt.get_data(1)
x = bt.get_stock_data("2014-03-06", cur_date, *stocklist)
con = pymysql.connect(host='localhost',
                      user='owenyang',
                      password='222121wj',
                      db='stock',
                      charset='utf8mb4',
                      cursorclass=pymysql.cursors.DictCursor)
with con:
    with con.cursor() as cursor:
        for i in x:
            for j in x[i].index:
                datecur = str(j)
                prices = x[i].loc[datecur]['Adj Close']
                if str(prices) == 'nan': prices = 0.0
                sql = "INSERT INTO stock.stockdata (Stocksymbol,Date,Prices) VALUES (" + "\'" + i.upper() + "\'" + "," + "\'" + datecur + "\'" + "," + "\'" + str(
                    prices) + "\'" ")"
                cursor.execute(sql)
    con.commit()
    with con.cursor() as cursor:
        cursor.execute("delete from stock.realdata")
        con.commit()
        cursor.execute("INSERT INTO stock.realdata SELECT  distinct Stocksymbol, Date, Prices FROM stock.stockdata")
        con.commit()

'''
frame = pd.read_sql("select * from stock.stockdata where Prices>=100",con)
for row in frame.iterrows():
    print(row[1]['Prices'])


'''


