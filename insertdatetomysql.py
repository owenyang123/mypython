import time, MySQLdb
conn=MySQLdb.connect(host="localhost",user="root",passwd="222121wj",db="owentest",charset="utf8")
cursor = conn.cursor()
a =range(1488)
for i in a:
    f1=open('D:\Python27\mypython\mysql\log1','r')
    f2=open('D:\Python27\mypython\mysql\log2','r')
    f3=open('D:\Python27\mypython\mysql\log3','r')
    f4=open('D:\Python27\mypython\mysql\log4','r')
    f5=open('D:\Python27\mypython\mysql\log5','r')
    f6=open('D:\Python27\mypython\mysql\log6','r')
    msg1=f1.readlines()[i]
    msg2=f2.readlines()[i]
    msg3=f3.readlines()[i]
    msg4=f4.readlines()[i]
    msg5=f5.readlines()[i]
    msg6=f6.readlines()[i]
    test1=[msg1,msg2,msg3,msg4,msg5,msg6]
    cursor.execute("insert into logdict values (%s,%s,%s,%s,%s,%s)", test1)
    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()
    f6.close()

conn.commit()
cursor.close()
conn.close()