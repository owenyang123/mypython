import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors

counter = 0 
while True:
	#Start config mode 
	dev = Device(host='vienne-re0.ultralab.juniper.net', user='labroot', password='lab123') 
	dev.open()  
	dev.timeout = 600
	cu = Config(dev)
	cu.rollback(1)
	cu.commit(timeout=600)
	counter += 1
	print "Round %s" % counter
	time.sleep(60)
	
	
