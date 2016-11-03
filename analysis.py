#coding=utf-8
from socket import *
import datetime, MySQLdb
import re,os
from time import strftime,localtime


def Gettimefromlog(string):
    year= str[16:20]
    if str[0:3]=='Jan':
        month='01'
    elif str[0:3]=='Feb':
        month='02'
    elif str[0:3]=='Mar':
       month='03'
    elif str[0:3]=='Apr':
       month='04'
    elif str[0:3]=='May':
        month='05'
    elif str[0:3]=='Jun':
        month='06'
    elif str[0:3]=='Jul':
        month='07'
    elif str[0:3]=='Aug':
        month='08'
    elif str[0:3]=='Sep':
        month='09'
    elif str[0:3]=='Oct':
        month='10'
    elif str[0:3]=='Nov':
        month='11'
    elif str[0:3]=='Dec':
        month='12'
    else:
        month='13'
    if str[4:5]==' ':
        days='0'+str[5:6]
    else:
        days=str[4:6]
    clock=str[7:15]
    if  month=='13':
        realtime='0000-00-00 00:00:00'
    else:
        realtime=year+'-'+month+'-'+days+' '+clock
    return realtime

x='*'
y='tblname'
z=''

def select(x,y,z):
    sql_content='select '+x+' from '+y+' '+z
    cursor.execute(sql_content)
    return  cursor.fetchall()

x='*'
y='tblname'
z=''
conn=MySQLdb.connect(host="localhost",user="root",passwd="222121wj",db="owentest",charset="utf8")
cursor = conn.cursor()
#get log count
x=' count(*) '
y='logcollecting'
z=' where analysisflag=0'
tmp=select(x,y,z)
linecount=int(tmp[0][0])

if linecount==0:
    print "Anylysis is not necessary"
    os._exit(0)
else:
    #built reg to match log
    x='*'
    y='logdict'
    z=''
    dict=[]
    for n in select(x,y,z):
        dict.append(n[0])
    #get log from syslogdb,do not forget change it to 1
    x=' * '
    y=' logcollecting '
    z=' where analysisflag=0  limit '+str(linecount)
    data_from_logcollecting=select(x,y,z)
    for row in data_from_logcollecting:
    #row[0] is time
    #row[1] is logbody
    #row[2] is ipaddr
    #row[3] is flag
    # insert flag,which means the log was read already
        cursor.execute("update logcollecting set analysisflag=1 where logdata=%s",row[1])
        # maps ip to name,time
        x=' * '
        y=' name_db '
        z='where ipaddr='+'\''+row[2]+'\''
        data_from_namedb=select(x,y,z)
        for name1 in data_from_namedb:
            boxname=name1[1]
        #check log
        for k in dict:
            find=False
            reg=re.compile(k)
            result=re.findall(reg,str(row[1]))
            if  len(result)==0:
                find=False
            else:
                find=True
                x=' * '
                y=' logdict '
                z=' where EventId='+'\''+str(k)+'\''
                dict_result=()
                for n in select(x,y,z):
                    dict_result=n
                break
        #logresult
        # 0 boxname,1 ipaddr,2 servertime/router time,3 log detail
        # 4 verndor name 5 event type,6 severity
        # 7 event description  8 action
        # 9 KB/PR/URL 10 count time
        if find:
            print row[1]
            routertime=Gettimefromlog(str(row[1]))
            log_result=[boxname,row[2],routertime,row[1],dict_result[7],dict_result[2],dict_result[3],dict_result[4],dict_result[5],dict_result[6],'0']
            count_default='0'
            cursor.execute("insert into analysis_result values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", log_result)
            conn.commit()

x=' * '
y=' analysis_result '
z=''
for n in select(x,y,z):
    t=n[7]
    x=' count(*) '
    y=' analysis_result '
    z=' where EventDescription='+'\''+str(t)+'\''
    tmp=select(x,y,z)
    freq=str(int(tmp[0][0]))
    cursor.execute("update analysis_result set counttimes=%s where EventDescription=%s",(freq,t))
    conn.commit()
cursor.close()
conn.close()
