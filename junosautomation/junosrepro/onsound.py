# onsound.py

import socket
import re
import time

host = "127.0.0.1"
username = "admin"
password = "KurwGDyd+oy+ZZ3S4qMn/wjeKOQ=" #encrypted password
port = 4444

#FUNCTIONS

def sendString(s):
	oculusock.sendall(s+"\r\n")
	print("> "+s)    

def waitForReplySearch(p):
    while True:
        servermsg = (oculusfileIO.readline()).strip()
        print(servermsg)
        if re.search(p, servermsg): 
            break
    return servermsg

#MAIN

#connect
oculusock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
oculusock.connect((host, port))
oculusfileIO = oculusock.makefile() 

#login 
waitForReplySearch("^<telnet> LOGIN")
sendString(username+":"+password)

sendString("publish mic")
time.sleep(2)
while True:
    sendString("setstreamactivitythreshold 0 10")
    waitForReplySearch("streamactivity: audio")
    sendString("speech please be quiet")
    time.sleep(5)

oculusfileIO.close()
oculusock.close()
