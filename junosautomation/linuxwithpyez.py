
from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.utils.start_shell import StartShell
import json
import os

'''
from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.utils.start_shell import StartShell
import json

def listroute(str1):
    if not str1:return None
    dev = Device(host = str1, user='labroot', password='lab123')
    dev.open()
    ss = StartShell(dev)
    ss.open()
    x=ss.run('cli -c "show route advertising-protocol bgp 10.85.209.89 |display json |no-more"')
    ss.close()
    dev.close()
    for i in x:
        z=json.dumps(i)
        with open('bgpls.json', 'w') as json_file:
            json.dump(z, json_file)
    return
listroute("10.85.174.57")

file read/write
with open('browsers.txt', 'w') as f:
    web_browsers = ['Firefox\n', 'Chrome\n', 'Edge\n']
    f.writelines("%s\n" % line for line in web_browsers)

import csv

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
sales = ['10', '8', '19', '12', '25']

with open('sales.csv', 'w') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',')
    csv_writer.writerow(weekdays)
    csv_writer.writerow(sales)
import json
with open('bgpls.json', 'r') as f:
    for i in f.readlines():
        x=i.replace("\\n ","\n")
        x=x.replace("\\r","").replace("\\","")
with open('bgpls1', 'w') as f:
    f.writelines(x)
def mail_notice(msg,maillist):
    for i in maillist:
        str2 = "sudo echo " + "\'" + msg + " " + " \'" + "| " + "mail -s " + "\'" + "core was found at 10.85.174.57 " + "\' " + i+" "
        try:os.system(str2)
        except:pass
    return
maillist= [" owenyang@juniper.net"," hfzhang@juniper.net"]
num=int(listroute("10.85.174.57"))
msg= str(num)+" "+" cores/core seen"
if num>=1:
    mail_notice(msg,maillist)
'''
def listnumcores(str1):
    if not str1:return None
    dev = Device(host = str1, user='labroot', password='lab123')
    dev.open()
    ss = StartShell(dev)
    ss.open()
    x=ss.run('cli -c "show system core-dumps |match root "')
    ss.close()
    dev.close()
    k=str(x[-1]).replace("%","")
    return k[44:]
def mail_notice(msg,maillist):
    for i in maillist:
        str2 = "sudo echo " + "\'" + msg + " " + " \'" + "| " + "mail -s " + "\'" + "core was found at 10.85.174.57 " + "\' " + i+" "
        try:os.system(str2)
        except:pass

maillist= [" owenyang@juniper.net"," hfzhang@juniper.net"]
listnumcores("10.85.174.57"))
msg= listnumcores("10.85.174.57"))
if num>=1:
    mail_notice(msg,maillist)
listnumcores("10.85.174.57")