from jnpr.junos import Device
import threading
from lxml import etree
import datetime
import re

list1=["dogmatix.ultralab.juniper.net"]

def dumprpc(str1):
    if not str1:return None
    cmdlist=["show system uptime no-forwarding","show version detail no-forwarding","show system core-dumps no-forwarding","show chassis alarms no-forwarding","show chassis hardware detail no-forwarding","show system processes extensive no-forwarding","show pfe statistics error","show pfe statistics traffic","show chassis routing-engine no-forwarding","show chassis environment no-forwarding","show chassis firmware no-forwarding","show chassis fpc detail","show system boot-messages  no-forwarding","show system storage no-forwarding","show system virtual-memory no-forwarding","show system buffer no-forwarding","show system queues no-forwarding","show system statistics no-forwarding","show configuration | except SECRET-DATA | display omit","show interfaces extensive no-forwarding","show chassis hardware extensive no-forwarding","show krt queue","show krt state","show route summary","show arp","show shmlog statistics logname all","show system subscriber-management detail","show subscribers summary","show database-replication summary","show database-replication statistics","show shm-ipc statistics","show system resource-monitor summary","show accounting server statistics","show accounting server statistics interim","show dhcp statistics verbose","show dhcpv6 statistics verbose","show dhcp server statistics verbose","show dhcp server binding summary","show dhcpv6 server statistics verbose","show dhcpv6 server binding summary","show dhcp relay statistics verbose","show dhcp relay binding summary","show dhcpv6 relay statistics verbose","show dhcpv6 relay binding summary","show ppp statistics extensive","show pppoe statistics","show services l2tp summary","show route forwarding-table summary","show network-access aaa statistics accounting","show network-access aaa statistics authentication detail","show network-access aaa statistics radius","show network-access aaa statistics volume-accounting"]
    x=[]
    dev = Device(host = str1, user='labroot', password='lab123')
    dev.open()
    for i in cmdlist:
        try:
            print i+" --> dev.rpc."+dev.display_xml_rpc(i).tag.replace("-","_")+"()"
        except:
            pass
    dev.close()
    return

dumprpc(list1[0])

