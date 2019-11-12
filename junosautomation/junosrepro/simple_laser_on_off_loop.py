import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device

counter = 0 

dev = Device(host='delhi-re0.ultralab.juniper.net', user='labroot', password='lab123')  
dev.open()

while counter < 1000000:
	#Laser off 
	pprint(dev.cli("request pfe execute command \"test xfp 4 laser off\" target fpc0"))  
	print "Waiting 30 seconds before onlining \n"
	time.sleep(30)
	#Laser on
	pprint(dev.cli("request pfe execute command \"test xfp 4 laser on\" target fpc0"))  
	print "Waiting 30 seconds before deactivating \n"
	counter = counter + 1
	print "This is round %s.\n" % (counter)
dev.close()
	
	
	
