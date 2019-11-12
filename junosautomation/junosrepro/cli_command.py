import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device

dev = Device(host='broadway-re0.ultralab.juniper.net', user='labroot', password='lab123')  
dev.open()  
print datetime.datetime.utcnow()
print "\nOfflining MIC 0\n"
pprint(dev.cli("request pfe execute command \"test mic detach 0\" target fpc0 | count"))  
print "Waiting 1 minute before onlining MIC\n"
print datetime.datetime.utcnow()
time.sleep(60)

pprint(dev.cli("request pfe execute command \"test mic attach 0 0\" target fpc0 | count"))
dev.close()  