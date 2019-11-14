#!/usr/bin/python
import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device

dev = Device(host='mango.ultralab.juniper.net', user='labroot', password='lab123')
dev.open()  
data = dev.facts
print data.keys()
print 'You successfully connected to router %s at %s' % (data['hostname'], datetime.datetime.utcnow())
dev.close() 





