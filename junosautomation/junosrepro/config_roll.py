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
	dev = Device(host='springbank.ultralab.juniper.net', user='labroot', password='lab123') 
	dev.open()  
	dev.timeout = 300
	cu = Config(dev)
	cu.rollback(1)
	cu.commit(timeout=360)
	counter += 1
	print "Round %s" % counter
	dev.close()
	time.sleep(60)
