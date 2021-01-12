'''
from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable

def listroute(str1):
    if not str1:return None
    dev = Device(host = str1, user='labroot', password='lab123')
    dev.open()
    routes = RouteTable(dev)
    routes.get(advertising_protocol_name="bgp", neighbor="10.85.209.89",extensive=True)
    for i in routes:print i
    dev.close()
    return
listroute("10.85.174.57")

'''

def findex(n):
    if n==1 or n==2:return 1
    temp1,temp2,temp3=1,1,1
    for i in range(3,n+1):
        temp3=temp1+temp2
        temp1=temp2
        temp2=temp3
    return temp3
for i in range(1,100):
    print findex(i)