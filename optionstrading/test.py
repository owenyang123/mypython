import MySQLdb
import seaborn as sns
import basictools as bt
import stockplay as sp
import pandas as pd
import csv
date=[bt.get_data(1)]
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()+['pdd',"sqqq","tqqq","pltr","qqq","vldr","SOXL"]
l=sp.caifuziyou(stocklist)
for i in range(len(l)):
    l[i]=l[i]+date
db = MySQLdb.connect("127.0.0.1","owenyang","222121wj","stock" )
cursor = db.cursor()
for i in l:
    sql="""INSERT INTO stockdata(Stocksymbol,
         Date, Prices)
         VALUES ('%s', '%s', '%f')"""% \
        (i[0],i[-1],i[1])
    cursor.execute(sql)
    db.commit()
db.close()