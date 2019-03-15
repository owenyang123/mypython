#import Lib
from socket import *
import datetime, MySQLdb
import re,os
#x content,y tblname z condition

#get input log
filename=raw_input("please input file name :")
if filename=="":
    print "please input the correct file name with path"
    print "Anylysis quits"
    os._exit(0)
logfiles=open(filename,"r")
if logfiles.read()=="" or logfiles.read()==None:
    print "Anylysis is not necessary"
    os._exit(0)
logfiles.close()

logfiles=open(filename,"r")
localmsg=[]
for line in logfiles:
    localmsg.append(line.lstrip("<0123456789>"))
###########################################################################
#get dict
def select(x,y,z):
    sql_content='select '+x+' from '+y+' '+z
    cursor.execute(sql_content)
    return  cursor.fetchall()
conn=MySQLdb.connect(host="172.25.89.200",user="owen123",passwd="lab123",db="junipertac",charset="utf8")
cursor = conn.cursor()
current_dict=select("*","junipertac_dictnew","")
# start analysis
find=False
dictlocal={}
for i in range(len(current_dict)):
    dictlocal[i]=(current_dict[i][0],current_dict[i][-2])

for j in localmsg:
    for i in dictlocal.keys():
        reg = re.compile(str(dictlocal[i][0]))
        result = re.findall(reg, str(j))
        if len(result)!=0:
            print "========================================"
            print j
            print "Approach to move forward"
            print dictlocal[i]
            print "-----------------------------------------"


#close socket
cursor.close()
conn.close()
logfiles.close()
