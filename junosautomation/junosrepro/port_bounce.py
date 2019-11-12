import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors

#First, clean up log files 

#MCR1.MIN
dev = Device(host='fuji.ultralab.juniper.net', user='labroot', password='lab123')
dev.open()
print 'Clearing MCR1.MIN logs'
dev.cli('clear log messages')
dev.cli('clear log MCR1.MIN.mpls.traceoptions.txt')
dev.close()

#MCR2.MIN
dev = Device(host='lisbon-re0.ultralab.juniper.net', user='labroot', password='lab123') 
dev.open()
print 'Clearing MCR2.MIN logs'
dev.cli('clear log messages')
dev.cli('clear log MCR2.MIN.mpls.traceoptions.txt')
dev.close()

#Currently bypassing MCR1.ENG due to hardware. 

#MCR1.ENG
#dev = Device(host='strut.ultralab.juniper.net', user='labroot', password='lab123') 
#dev.open()
#print 'Clearing MCR1.ENG logs'
#dev.cli('clear log messages')
#dev.cli('clear log MCR1.ENG.mpls.traceoptions.txt')
#dev.close()

#Starting the test on R3.Denver
#R3.Denver
dev = Device(host='nick.ultralab.juniper.net', user='labroot', password='lab123')
print datetime.datetime.utcnow()
print 'Opening connection to R3.Denver ...'
dev.open()  
print 'Clearing R3.Denver logs'
dev.cli('clear log messages')
dev.cli('clear log R3.Denver.mpls.traceoptions.txt')

counter = 100
while counter >= 0:
	counter -= 1
	print counter 
	#Start config mode 
	cu = Config(dev)
	print datetime.datetime.utcnow()
	print 'Disabling ae1 interfaces ...'
	set_cmd = 'set interfaces ge-0/0/0 disable'
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/0/1 disable'           
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/0/2 disable'           
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/0/3 disable'           
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/1/0 disable'           
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/1/1 disable'           
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/1/2 disable'           
	cu.load(set_cmd, format='set')
	set_cmd = 'set interfaces ge-0/1/3 disable' 
	cu.load(set_cmd, format='set')

	#disable the links towards MCR.ENG
#	set_cmd = 'set interfaces ge-0/2/0 disable'
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/3/0 disable' 
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/2/1 disable' 
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/3/1 disable' 
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/2/2 disable' 
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/3/2 disable' 
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/2/3 disable' 
#	cu.load(set_cmd, format='set')
#	set_cmd = 'set interfaces ge-0/3/3 disable' 
#	cu.load(set_cmd, format='set')
	print 'Committing'
	cu.commit()
	
	#ports now down 
	print datetime.datetime.utcnow()
	print 'Interfaces down, waiting 3 seconds'
	time.sleep(3)
	cu.rollback(1)
	cu.commit()
	
	#ports now up
	print datetime.datetime.utcnow()
	print 'Interfaces up, waiting 8 seconds'
	time.sleep(8)
	cu.rollback(1)
	cu.commit()
	
	#ports now down
	print datetime.datetime.utcnow()
	print 'Interfaces down, waiting 26 seconds'
	time.sleep(26)
	cu.rollback(1)
	cu.commit()
	
	#ports now up
	print datetime.datetime.utcnow()
	print 'Interfaces are up, waiting 130 seconds'  
	time.sleep(130)
	cu.rollback(1)
	cu.commit()
	
	#ports now down 
	print datetime.datetime.utcnow()
	print 'Interfaces down, waiting 25 seconds'
	time.sleep(25)
	cu.rollback(1)
	cu.commit()
	print 'Interfaces up, waiting 10 minutes before restarting test...'
	time.sleep(600)
print datetime.datetime.utcnow()
print 'Interfaces up, ending test'
dev.close()  