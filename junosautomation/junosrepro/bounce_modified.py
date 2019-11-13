#/usr/bin/python
import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
import warnings 
from jnpr.junos.op.phyport import PhyPortErrorTable
from jnpr.junos.op.voq import VoqTable

dev = Device(host = 'portland-re1.ultralab.juniper.net', user='labroot', password='lab123')  
dev.open()  
print datetime.datetime.utcnow()
counter = 0 
with open('sample.csv','a') as myfile:
	myfile.write("%s,%s,%s\n" % (('Time'),('Carrier Transition'),('Forwarding-Class')))
while counter < 1000:
	#Offline et-3/1/1 laser 
	pprint(dev.cli("request pfe execute command \"test cfp 2 laser off\" target fpc3"))  
	print "Waiting 30 seconds before onlining \n"
	time.sleep(30)

	#Online et-3/1/1 laser 
	pprint(dev.cli("request pfe execute command \"test cfp 2 laser on\" target fpc3"))
	#time.sleep(30)
	#Determine way to spit out results in readable format for drops
    #Number of drops per que:
	#Delta compared to the last result
	print '\n\n Waiting 1 minutes before repeating test'
    #Count carrier transitions 
	tblError = PhyPortErrorTable(dev)
	tblError.get(interface_name='et-1/1/0')
	for item in tblError:
		counter = item.tx_err_carrier_transitions
	#Get Forwarding class
	tblVoq = VoqTable(dev)
	tblVoq.get(interface_name='et-1/1/0')
	for item in tblVoq:
		forwarding_class = item.voq_forwarding_class_name
		drops = item.voq_counters_drop_packets
		fc_be = forwarding_class[0]
		fc_video = forwarding_class[4]
		fc_be_drops = drops[5]
		fc_video_drops = drops[213]	
	print "Current counter value is %s." % (counter) 
	with open('sample.csv','a') as myfile:
		myfile.write("%s,%s,%s,%s\n" % ((str(datetime.datetime.utcnow())),(str(counter)),(str(fc_be)),(str(fc_video))))
		myfile.write("%s,%s,%s,%s\n" % ((''),(''),(str(fc_be_drops)),(str(fc_video_drops))))
	time.sleep(60)

dev.close()  

