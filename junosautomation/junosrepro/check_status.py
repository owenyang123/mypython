import sys
import time 
import datetime
from lxml import etree
from pprint import pprint  
from jnpr.junos import Device
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors
from mail_message import Email_Alert

#Start connection and enter confif mode 

dev = Device(host='springdawn.ultralab.juniper.net', user='labroot', password='lab123') 
dev.open()  
dev.timeout = 300
cu = Config(dev)

#indent this to log everything 


#Start loop 
while True: 
	#with open('data.txt','a') as myfile:
	#disable ae0 
	
	set_cmd = 'set interfaces ae0 disable'           
	cu.load(set_cmd, format='set')
	
	#commit 
	
	cu.commit()
	
	#check ae0 is down 
	
	check_ae_status=dev.rpc.get_interface_information(interface_name="ae0", terse=True, normalize=True)
	current_ae_status=(check_ae_status.xpath(".//admin-status")[0].text)
	
	print "\n"
	print datetime.datetime.utcnow()
	print "==== INTERFACE DOWN START ===="
	if current_ae_status in ['down']:
		print "Interface is down"
	else:
		print "Interface is up, aborting."
		dev.close()
		sys.exit()
			
	#check route for ae0 
	
	verify_nh=dev.rpc.get_route_information(destination="78.140.145.148", normalize=True)
	nh1=(verify_nh.xpath(".//rt-entry/nh/via")[0].text)
	try:
		nh2=(verify_nh.xpath(".//rt-entry/nh/via")[1].text)
		print "NH2 is valid and ae0 is down!  Condition met"
		print "NH2 is %s" % (nh2)
		print "AE status is %s." % (current_ae_status)
		Email_Alert()
		dev.close()
		sys.exit()
	except IndexError: 
		nh2 = "NULL" 
		pass
	#Print everything out 
	print "AE status is currently %s." % (current_ae_status)
	print "NH1 status is currently %s." % (nh1)
	print "NH2 status is currently %s." % (nh2) 
	print "==== INTERFACE DOWN END ===="
	
	#Reverse everything 
	
	#enable ae0 
	
	set_cmd = 'delete interfaces ae0 disable'           
	cu.load(set_cmd, format='set')
	
	#commit 
	
	cu.commit()
	
	#check ae0 is up 
	
	check_ae_status=dev.rpc.get_interface_information(interface_name="ae0", terse=True, normalize=True)
	current_ae_status=(check_ae_status.xpath(".//admin-status")[0].text)
	
	print "\n"
	print "==== INTERFACE UP START ===="
	print datetime.datetime.utcnow()
	if current_ae_status in ['up']:
		print "Interface is up"
	else:
		print "Interface is down, aborting."
		dev.close()
		sys.exit()
		
	#sleep a moment giving time for interface to come up and route to program 
	time.sleep(45)
	
	#check route for ae0  nh's
	
	verify_nh=dev.rpc.get_route_information(destination="78.140.145.148", normalize=True)
	nh1=(verify_nh.xpath(".//rt-entry/nh/via")[0].text)
	nh2=(verify_nh.xpath(".//rt-entry/nh/via")[1].text)
	
	#Print everything out 
	
	print "AE status is currently %s." % (current_ae_status)
	print "NH1 status is currently %s." % (nh1)
	print "NH2 status is currently %s." % (nh2)
	print "==== INTERFACE UP END ===="
