
from socket import *
import datetime, MySQLdb
from time import strftime,localtime

conn=MySQLdb.connect(host="localhost",user="root",passwd="222121wj",db="owentest",charset="utf8")
cursor = conn.cursor()
cursor.execute("select * from logdict")
print cursor.fetchall()

conn.commit()
cursor.close()
conn.close()

