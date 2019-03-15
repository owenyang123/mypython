from socket import *
import datetime, MySQLdb
import re,os
#x content,y tblname z condition


#get input log
logfiles=open("log.txt","r")


#get dict
def select(x,y,z):
    sql_content='select '+x+' from '+y+' '+z
    cursor.execute(sql_content)
    return  cursor.fetchall()
conn=MySQLdb.connect(host="172.25.89.200",user="owen123",passwd="lab123",db="junipertac",charset="utf8")
cursor = conn.cursor()

dict1=select("*","junipertac_dictnew","")
#close socket
cursor.close()
conn.close()
logfiles.close()
