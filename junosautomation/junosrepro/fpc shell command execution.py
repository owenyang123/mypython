import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
import warnings 

print "This script will offline the MIC, wait one minute, and then online the MIC for a device you specify.\n\n"

print "NETCONF ssh must be enabled on the device in order for this script to connect!\n\n"

hostDevice = raw_input('Enter Device Name or IP address: ')

dev = Device(host = hostDevice, user='labroot', password='lab123')  
dev.open()  

print datetime.datetime.utcnow()
print "\nOfflining MIC 0\n"

pprint(dev.cli("request pfe execute command \"test mic detach 0\" target fpc0"))  

print "Waiting 1 minute before onlining MIC\n"
print datetime.datetime.utcnow()

time.sleep(60)

pprint(dev.cli("request pfe execute command \"test mic attach 0 0\" target fpc0"))

print '\n\nMIC should now be online'

dev.close()  