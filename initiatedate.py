# coding="utf-8"
import numpy as np
import MySQLdb
import sqlfun
import datetime
import csv



conn=MySQLdb.connect(host="localhost",user="root",passwd="222121wj",db="stock",charset="utf8")
cursor = conn.cursor()


reader = csv.reader(file('goog.csv', 'rb'))
for line in reader:
   t=str(line[0]).split('/')
   s='20'+t[2]+'-'+t[0]+'-'+t[1]
   date1=str(datetime.datetime.strptime(s, "%Y-%m-%d").date())
   values=[date1,float(line[1]),float(line[2]),float(line[3]),float(line[4]),float(line[5])]
   print values
   cursor.execute('insert into goog values(%s,%s,%s,%s,%s,%s)',values)
   conn.commit()

cursor.close()
conn.close()


