from socket import *
import datetime, MySQLdb
from time import strftime,localtime

host = "0.0.0.0"
port = 9999
buf = 9000
addr = (host,port)
# Create socket and bind to address
UDPSock = socket(AF_INET,SOCK_DGRAM)
UDPSock.bind(addr)
# Receive messages
conn=MySQLdb.connect(host="localhost",user="root",passwd="222121wj",db="owentest",charset="utf8")
cursor = conn.cursor()
while 1:
    data,addr = UDPSock.recvfrom(buf)
    if not data:
        print "Client has exited!"
        break
    else:
        print data
        text1=data.lstrip('<0123456789>')
        ip= str(addr[0])
        t1= str('%s' %strftime('%Y-%m-%d %H:%M:%S',localtime()))
        flag='0'
        cursor.execute("insert into logcollecting values (%s,%s,%s,%s)", (t1,text1,ip,flag))
        conn.commit()

# Close socket
UDPSock.close()
cursor.close()
conn.close()
