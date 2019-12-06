#/usr/bin/python
#set system login class server permissions configure
#set system login class server permissions view
#set system login class server permissions view-configuration
#set system login class server allow-configuration "interfaces xe-5/1/2 unit .* vlan-id .*"

#Get a list of all the interfaces on the box that match ge/xe/et. 
#Delete the exception interfaces from the list 
#Generate allow-configuration for box 

import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.op.phyport import *

dev = Device(host = 'weir-re0.ultralab.juniper.net', user='labroot', password='lab123')  
dev.open()  

#grab all interfaces 
ports = PhyPortTable(dev).get()
port_names = []
for port in ports:
    port_names.append(port.key)
	
#build exclusion list 
port_exclude = ['xe-5/1/2', 'xe-0/3/1']

#remove port-exclude entries from port_names list put them in whitelist_ports
whitelist_ports = [x for x in port_names if x not in port_exclude]

#generate config 
config_whitelist_ports = []
for item in whitelist_ports:
	config_whitelist_ports.append('set system login class server allow-configuration "interfaces ' + item + ' unit .* vlan-id .*"')

for item in config_whitelist_ports: 
	print item
	
#Example output 
#set system login class server allow-configuration "interfaces xe-0/0/0 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/0/1 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/0/2 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/0/3 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/1/0 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/1/1 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/1/2 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/1/3 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/2/0 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/2/1 unit .* vlan-id .*"
#set system login class server allow-configuration "interfaces xe-0/2/2 unit .* vlan-id .*"

dev.close()

	
 

str123="12312312313ae"

