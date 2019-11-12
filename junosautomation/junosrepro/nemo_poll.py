import sys
import time 
import datetime
from lxml import etree
from pprint import pprint  
from jnpr.junos import Device

while True: 

	dev = Device(host='nemo-re0.ultralab.juniper.net', user='labroot', password='lab123') 
	dev.open()
	#fstats = dev.rpc.get_fabric_queue_information()
	#fstats1 = dev.rpc.get_software_information()
	#fstats1 = dev.rpc.get_system_uptime_information()
	fstats2 = dev.rpc.get_route_engine_information()
	#fstats3 = dev.rpc.get_alarm_information()
	#fstats4 = dev.rpc.get_environment_information()
	#fstats5 = dev.rpc.get_interface_information()
	#fstats6 = dev.rpc.get_interface_queue_information()
	#fstats7 = dev.rpc.get_isis_interface_information()
	#fstats9 = dev.rpc.get_bgp_neighbor_information()
	#fstats10 = dev.rpc.get_ldp_traffic_statistics_information()
	#fstats11 = dev.rpc.get_interface_optics_diagnostics_information()
	#fstats14 = dev.rpc.get_ccc_information()
	#fstats17 = dev.rpc.get_firewall_information()
	#fstats18 = dev.rpc.get_policer_information()
	#fstats20 = dev.rpc.get_fpc_information()
	with open('nemo_data.txt','a') as myfile:
		myfile.write(str(datetime.datetime.utcnow()))
		#myfile.write(str((etree.tostring(fstats1))))
		myfile.write(str((etree.tostring(fstats2))))
		#myfile.write(str((etree.tostring(fstats3))))
		#myfile.write(str((etree.tostring(fstats4))))
		#myfile.write(str((etree.tostring(fstats5))))
		#myfile.write(str((etree.tostring(fstats6))))
		#myfile.write(str((etree.tostring(fstats7))))
		#myfile.write(str((etree.tostring(fstats9))))
		#myfile.write(str((etree.tostring(fstats10))))
		#myfile.write(str((etree.tostring(fstats11))))
		#myfile.write(str((etree.tostring(fstats14))))
		#myfile.write(str((etree.tostring(fstats17))))
		#myfile.write(str((etree.tostring(fstats18))))
		#myfile.write(str((etree.tostring(fstats20))))
	dev.close()
	time.sleep(300)
	
