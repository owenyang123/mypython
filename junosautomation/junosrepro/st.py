#!/usr/bin/python
import os
import time
count =0
i_input=0
while (count < 100):
    time1=time.time()
    input=int(os.popen("snmpget -v2c -Cf -c test -O t 172.19.163.93 1.3.6.1.2.1.31.1.1.1.6.503").read().split()[3])
    time2=time.time()
    print time2-time1
    rate = (input-i_input)*8/30
    time3=time.time()
    print time3-time2
    i_input=input    
    count=count+1
