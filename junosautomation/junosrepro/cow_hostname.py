import os, sys, time, datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors

#Create backup directory 
current_timestamp = datetime.datetime.utcnow()

#define lab username and passwords
router_name = 'd26-22.ultralab.juniper.net'  
user_name = 'root'
lab_password = 'Juniper'

#List of commands  
command_list1 = ['delete interfaces xe-0/0/2:2', 'set interfaces xe-0/0/2:2 unit 0 apply-macro pfab ifl_id 738', 'set interfaces xe-0/0/2:2 unit 0 apply-macro pfab vc_id 1404', 'set interfaces xe-0/0/2:2 description test' ]
command_list2 = [ 'delete interfaces xe-0/0/2:2', 'set interfaces xe-0/0/2:2 unit 3301 apply-macro pfab ifl_id 737', 'set interfaces xe-0/0/2:2 unit 3301 apply-macro pfab service evpn', 'set interfaces xe-0/0/2:2 unit 3301 apply-macro pfab vc_id 1405', 'set interfaces xe-0/0/2:2 description test']
command_list3 = ['delete interfaces xe-0/0/2:2', 'set interfaces xe-0/0/2:2 unit 0 apply-macro pfab ifl_id 738', 'set interfaces xe-0/0/2:2 unit 0 apply-macro pfab vc_id 1404', 'set interfaces xe-0/0/2:2 description test']
command_list4 = ['delete interfaces xe-0/0/2:2', 'set interfaces xe-0/0/2:2 unit 402 apply-macro pfab ifl_id 773', 'set interfaces xe-0/0/2:2 unit 402 apply-macro pfab vc_id 1425', 'set interfaces xe-0/0/2:2 unit 402 apply-macro pfab service evpn', 'set interfaces xe-0/0/2:2 description test']
command_list5 = ['set interfaces xe-0/0/2:2 unit 498 apply-macro pfab ifl_id 777', 'set interfaces xe-0/0/2:2 unit 498 apply-macro pfab vc_id 1427', 'set interfaces xe-0/0/2:2 unit 498 apply-macro pfab service evpn', 'set interfaces xe-0/0/2:2 description test']

dev = Device(host=router_name, user=user_name, password=lab_password)
dev.open()

while True:
	for commands in command_list1:
		cu = Config(dev)
		cu.load(commands, format='set')
	cu.commit()
	print 'Done list 1'
	
	for commands in command_list2:
		cu = Config(dev)
		cu.load(commands, format='set')
	cu.commit()
	print 'Done list 2'
	
	for commands in command_list3:
		cu = Config(dev)
		cu.load(commands, format='set')
	cu.commit()
	print 'Done list 3'
	
	for commands in command_list4:
		cu = Config(dev)
		cu.load(commands, format='set')
	cu.commit()
	print 'Done list 4'
	
	for commands in command_list5:
		cu = Config(dev)
		cu.load(commands, format='set')
	cu.commit()
	print 'Done list 5'


#Example of command list 1 working 
#Dec 12 19:28:21.536  cfr2.wdc2 mgd[88311]: UI_NETCONF_CMD: User 'root' used NETCONF client to run command 'load-configuration action="set" format="text"'
#Dec 12 19:28:21.537  cfr2.wdc2 mgd[88311]: Could not send message to eventd
#Dec 12 19:28:21.537  cfr2.wdc2 mgd[88311]: UI_CMDLINE_READ_LINE: User 'root', command 'hello capabilities capability urn:ietf:params:netconf:capability:writable-running:1.0 capability capability urn:ietf:params:netconf:capability:rollback-on-error:1.0 capability capability urn:liberouter:params:netconf:capability:power-control:1.0 capability capability urn:ietf:params:netconf:capability:validate:1.0 capability capability urn:ietf:params:netconf:capability:confirmed-commit:1.0 capability capability "urn:ietf:params:netconf:capability:url:1.0?scheme=http,ftp,file,https,sftp" capability capability urn:ietf:params:netconf:base:1.0 capability capability urn:ietf:params:netconf:base:1.1 capability capability urn:ietf:params:netconf:capability:candidate:1.0 capability capability urn:ietf:params:netconf:capability:notification:1.0 capability capability urn:ietf:params:netconf:capability:xpath:1.0 capability capability urn:ietf:params:netconf:capability:startup:1.0 capability capability urn:ietf:params:netconf:capabi
#Dec 12 19:28:21.537  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_OTHER: User 'root' delete: [interfaces xe-0/0/2:2]
#Dec 12 19:28:21.643  cfr2.wdc2 mgd[88311]: UI_NETCONF_CMD: User 'root' used NETCONF client to run command 'load-configuration action="set" format="text"'
#Dec 12 19:28:21.644  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_OTHER: User 'root' set: [interfaces xe-0/0/2:2 unit 0]
#Dec 12 19:28:21.644  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_OTHER: User 'root' set: [interfaces xe-0/0/2:2 unit 0 apply-macro pfab]
#Dec 12 19:28:21.645  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_OTHER: User 'root' set: [interfaces xe-0/0/2:2 unit 0 apply-macro pfab ifl_id]
#Dec 12 19:28:21.645  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_SET: User 'root' set: [interfaces xe-0/0/2:2 unit 0 apply-macro pfab ifl_id] "738 -> "738"
#Dec 12 19:28:21.645  cfr2.wdc2 mgd[88311]: UI_CMDLINE_READ_LINE: User 'root', command 'load-configuration rpc rpc load-configuration set interfaces xe-0/0/2:2 unit 0 apply-macro pfab ifl_id 738 '
#Dec 12 19:28:21.749  cfr2.wdc2 mgd[88311]: UI_NETCONF_CMD: User 'root' used NETCONF client to run command 'load-configuration action="set" format="text"'
#Dec 12 19:28:21.750  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_OTHER: User 'root' set: [interfaces xe-0/0/2:2 unit 0 apply-macro pfab vc_id]
#Dec 12 19:28:21.750  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_SET: User 'root' set: [interfaces xe-0/0/2:2 unit 0 apply-macro pfab vc_id] "1404 -> "1404"
#Dec 12 19:28:21.750  cfr2.wdc2 mgd[88311]: UI_CMDLINE_READ_LINE: User 'root', command 'load-configuration rpc rpc load-configuration set interfaces xe-0/0/2:2 unit 0 apply-macro pfab vc_id 1404 '
#Dec 12 19:28:21.854  cfr2.wdc2 mgd[88311]: UI_NETCONF_CMD: User 'root' used NETCONF client to run command 'load-configuration action="set" format="text"'
#Dec 12 19:28:21.855  cfr2.wdc2 mgd[88311]: UI_CFG_AUDIT_SET: User 'root' set: [interfaces xe-0/0/2:2 description] "test -> "test"









 






