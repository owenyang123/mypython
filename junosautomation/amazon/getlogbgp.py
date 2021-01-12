from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.utils.start_shell import StartShell
import json
import os
import csv
import threading
def getlog(str1):
    if not str1:return None
    try:
        dev = Device(host = str1, user='labroot', password='lab123')
        dev.open()
        ss = StartShell(dev)
        ss.open()
        x=ss.run('cli -c "show log messages|no-more "')
        ss.close()
        dev.close()
        with open(str1 + "log" + ".csv", 'w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',')
            for i in x[-1].split("\n"):
                csv_writer.writerow([i.replace("\n","")])
    except:
        print str1+" is not reachable"
        pass
    return
def getbgp(str1):
    try:
        if not str1:return None
        dev = Device(host = str1, user='labroot', password='lab123')
        dev.open()
        ss = StartShell(dev)
        ss.open()
        x=ss.run('cli -c "show bgp summary |no-more |match est "')
        ss.close()
        dev.close()
        with open(str1 + "bgp" + ".csv", 'w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',')
            for i in x[-1].split("\n"):
                csv_writer.writerow([i.replace("\n","")])
    except:
        print str1 + " is not reachable"
        pass
    return
list1=["erebus.ultralab.juniper.net","hypnos.ultralab.juniper.net","moros.ultralab.juniper.net","norfolk.ultralab.juniper.net","alcoholix.ultralab.juniper.net","antalya.ultralab.juniper.net","automatix.ultralab.juniper.net","beltway.ultralab.juniper.net","bethesda.ultralab.juniper.net","botanix.ultralab.juniper.net","dogmatix.ultralab.juniper.net","getafix.ultralab.juniper.net","idefix.ultralab.juniper.net","kratos.ultralab.juniper.net","pacifix.ultralab.juniper.net","photogenix.ultralab.juniper.net","rio.ultralab.juniper.net","matrix.ultralab.juniper.net","cacofonix.ultralab.juniper.net","asterix.ultralab.juniper.net","timex.ultralab.juniper.net","greece.ultralab.juniper.net","holland.ultralab.juniper.net","nyx.ultralab.juniper.net","atlantix.ultralab.juniper.net","obelix.ultralab.juniper.net","camaro.ultralab.juniper.net","mustang.ultralab.juniper.net"]

instance=[]
for i in list1:
    trd=threading.Thread(target=getlog,args=(i,))
    trd.start()
    instance.append(trd)
for thread in instance:
    thread.join()

instance=[]
for i in list1:
    trd=threading.Thread(target=getbgp,args=(i,))
    trd.start()
    instance.append(trd)
for thread in instance:
    thread.join()
'''
 cat messages | grep "IF_MSG_IFD_BULK_MUP_DOWN" | awk '{print $7}' | sort | uniq -c
 
 cat messages | grep BGP | awk -F" " '{ for (x=4; x<=20; x++) printf("%s ", $x);printf("\n"); }' | sort -n -k 4 | uniq -c
'''