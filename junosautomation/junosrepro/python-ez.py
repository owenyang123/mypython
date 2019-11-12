from pprint import pprint  
from jnpr.junos import Device

dev = Device(host='192.168.1.6', user='TEMP', password='')  
dev.open()  
pprint(dev.facts)  
dev.close()  