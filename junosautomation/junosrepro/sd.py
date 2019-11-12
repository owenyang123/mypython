#!/usr/bin/python
import os
import time
import datetime
count = 0

i_input=int(os.popen("snmpget -v2c -Cf -c test -O t 172.19.163.93 1.3.6.1.2.1.31.1.1.1.6.503").read().split()[3])
i_output=int(os.popen("snmpget -v2c -Cf -c test -O t 172.19.163.93 1.3.6.1.2.1.31.1.1.1.10.503").read().split()[3])
time.sleep(10)
while (count >= 0):
    t1=time.time()
    input=int(os.popen("snmpget -v2c -Cf -c test -O t 172.19.163.93 1.3.6.1.2.1.31.1.1.1.6.503").read().split()[3])
    tg=time.time()-t1    
    output=int(os.popen("snmpget -v2c -Cf -c test -O t 172.19.163.93 1.3.6.1.2.1.31.1.1.1.10.503").read().split()[3])
    now = datetime.datetime.now()
    ct1 = now.strftime("%Y-%m-%d %H:%M:%S")
    if input-i_input < 0:
        i_rate = (input+18446744073709551616-i_input)*8/10/1000
    else:
        i_rate = (input-i_input)*8/10/1000
    if output-i_output < 0:
        o_rate = int((output+18446744073709551616-i_output)*8/(10-tg)/1000)
    else:
        o_rate = int((output-i_output)*8/(10-tg)/1000)
    print ct1,"  current input rate is:",i_rate," kbps","  current output rate is:",o_rate," kbps"
    i_input=input
    i_output=output
    tg2=float(10)-(time.time()-t1)    
    time.sleep(tg2)
    count=count+1
