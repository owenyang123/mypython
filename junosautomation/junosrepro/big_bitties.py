import sys
import time 
import datetime
from lxml import etree
from pprint import pprint  
from jnpr.junos import Device

router_name = 'd26-22.ultralab.juniper.net'  
user_name = 'root'
lab_password = 'Juniper'

dev = Device(host=router_name, user=user_name, password=lab_password)
dev.open()

while True: 
	fstats1 = dev.rpc.get_alarm_information()
	fstats2 = dev.rpc.get_environment_information()
	fstats3 = dev.rpc.get_fpc_information()
	fstats4 = dev.rpc.get_interface_information()
	fstats5 = dev.rpc.get_interface_optics_diagnostics_information()
	fstats6 = dev.rpc.get_chassis_inventory()	
	with open('data.txt','a') as myfile:
		myfile.write(str(datetime.datetime.utcnow()))
		myfile.write(str((etree.tostring(fstats1))))
		myfile.write(str((etree.tostring(fstats2))))
		myfile.write(str((etree.tostring(fstats3))))
		myfile.write(str((etree.tostring(fstats4))))
		myfile.write(str((etree.tostring(fstats5))))
		myfile.write(str((etree.tostring(fstats6))))
	time.sleep(1)
	
