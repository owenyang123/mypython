#!/usr/bin/python
#jbrantley@juniper.net

def Archive_Set():
	import sys
	import time 
	import datetime
	from pprint import pprint  
	from jnpr.junos import Device
	from jnpr.junos.utils.config import Config
	device = raw_input("Enter hostname or IP of target system: ")
	#print "Setting archiving on " + device + ". Please wait..."
	dev = Device(host=device, user='labroot', password='lab123')  
	dev.open()  
	#print "Connection opened to " + device + " ..."
	with Config(dev, mode='private') as cu: 
		set_transfer = "set system archival configuration transfer-on-commit"
		set_location = "set system archival configuration archive-sites \"scp://labroot@10.85.47.53:/home/labroot/lab_archives\" password lab123\""
		cu.load(set_transfer, format='set')
		cu.load(set_location, format='set')
		cu.commit()
		print 'You successfully commited archiving to router %s at %s' % (device, datetime.datetime.utcnow().strftime("%Y-%m-%d @ %H:%M"))
		print 'Closing connection to %s.  Goodbye!\n' % device 
	dev.close() 

def Archive_Set_Multiple():
	import sys
	import time 
	import datetime
	from pprint import pprint  
	from jnpr.junos import Device
	from jnpr.junos.utils.config import Config
	user_name='labroot'
	lab_password='lab123'
	
	device_list = ['submariner-re0.ultralab.juniper.net', 'd19-37.ultralab.juniper.net' ]
	for taget_system in device_list:
		dev = Device(host=taget_system, user=user_name, password=lab_password)
		dev.open()
		with Config(dev, mode='private') as cu: 
			set_transfer = "set system archival configuration transfer-on-commit"
			set_location = "set system archival configuration archive-sites \"scp://labroot@10.85.47.53:/home/labroot/lab_archives\" password lab123\""
			cu.load(set_transfer, format='set')
			cu.load(set_location, format='set')
			cu.commit()
			print 'You successfully commited archiving to router %s at %s' % (taget_system, datetime.datetime.utcnow().strftime("%Y-%m-%d @ %H:%M"))
			print 'Closing connection to %s.  Goodbye!\n' % taget_system 
		dev.close() 

	





