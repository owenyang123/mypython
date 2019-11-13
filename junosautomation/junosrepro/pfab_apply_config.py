import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors

#set system services netconf ssh must be enabled, or it will error out 


#dev contains the box you want to open and the credentials 
dev = Device(host='flagstaff-re0.ultralab.juniper.net', user='labroot', password='lab123')
dev.open()

#Start config mode 
cu = Config(dev)

#Here is an example of deleting something within the config - just give the full set command 
#commit-0-00:47:52.034 - viki
set_cmd = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.200.1'
cu.load(set_cmd, format='set')

set_cmd1 = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.200.1 description CFR1.HOU1'
cu.load(set_cmd1, format='set')

set_cmd2 = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.200.2'
cu.load(set_cmd2, format='set')

set_cmd3 = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.200.2 description CFR2.HOU1 '
cu.load(set_cmd3, format='set')

cu.commit()
#code working up to this point above need to continue modifying the set_cmd# for each cmd you are going to run at the time before the commit - can reuse the numbers after commit

set_cmd = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.196.1'
cu.load(set_cmd, format='set')

set_cmd = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.196.1 description CFR1.JAX1'
cu.load(set_cmd, format='set')

set_cmd = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.196.2'
cu.load(set_cmd, format='set')

set_cmd = 'set protocols bgp group IBGP-Underlay-Core neighbor 172.16.196.2 description CFR2.JAX1'
cu.load(set_cmd, format='set')

#this line is needed after the set command to actually apply it to the box 
#cu.load(set_cmd, format='set')

#This issues the commit. 
cu.commit()

#Here is an example of adding something within the config 
#commit - Aug 27 04:37:55.810 - rmc
set_cmd = 'delete interfaces xe-0/0/0:0 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/0:0 description pfab_macro'

set_cmd = 'delete interfaces xe-0/0/0:1 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/0:1 disable'
set_cmd = 'set interfaces xe-0/0/0:1 description avaliable'

set_cmd = 'delete interfaces xe-0/0/0:2 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/0:2 disable'
set_cmd = 'set interfaces xe-0/0/0:2 description avaliable'

set_cmd = 'delete interfaces xe-0/0/0:3 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/0:3 disable'
set_cmd = 'set interfaces xe-0/0/0:3 description avaliable'

set_cmd = 'delete interfaces xe-0/0/1:1 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/1:1 disable'
set_cmd = 'set interfaces xe-0/0/1:1 description avaliable'

set_cmd = 'delete interfaces xe-0/0/1:2 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/1:2 disable'
set_cmd = 'set interfaces xe-0/0/1:2 description avaliable'

set_cmd = 'delete interfaces xe-0/0/1:3 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/1:3 disable'
set_cmd = 'set interfaces xe-0/0/1:3 description avaliable'

set_cmd = 'delete interfaces xe-0/0/2:2 apply-macro wiring'
set_cmd = 'set interfaces xe-0/0/2:2 disable'
set_cmd = 'set interfaces xe-0/0/2:2 description avaliable'

set_cmd = 'delete interfaces xe-0/0/2:3 unit 102 apply-macro pfab'
set_cmd = 'delete interfaces xe-0/0/2:3 unit 103 apply-macro pfab'
set_cmd = 'delete interfaces xe-0/0/2:3 unit 104 apply-macro pfab'
set_cmd = 'delete interfaces xe-0/0/2:3 apply-macro wiring'

set_cmd = 'set interfaces xe-0/0/2:3 disable'
set_cmd = 'set interfaces xe-0/0/3:0 disable'
set_cmd = 'set interfaces xe-0/0/3:1 disable'
set_cmd = 'set interfaces xe-0/0/3:2 disable'
set_cmd = 'set interfaces xe-0/0/3:3 disable'
set_cmd = 'set interfaces xe-0/0/4:0 disable'
set_cmd = 'set interfaces xe-0/0/4:1 disable'
set_cmd = 'set interfaces xe-0/0/4:2 disable'
set_cmd = 'set interfaces xe-0/0/4:3 disable'
set_cmd = 'set interfaces xe-0/0/5:0 disable'
set_cmd = 'set interfaces xe-0/0/5:1 disable'
set_cmd = 'set interfaces xe-0/0/5:2 disable'
set_cmd = 'set interfaces xe-0/0/5:3 disable'
set_cmd = 'set interfaces et-0/0/6 disable'
set_cmd = 'set interfaces et-0/0/7 disable'
set_cmd = 'set interfaces et-0/0/8 disable'
set_cmd = 'set interfaces et-0/0/9 disable'
set_cmd = 'set interfaces et-0/0/10 disable'
set_cmd = 'set interfaces et-0/0/11 disable'

set_cmd = 'delete interfaces et-1/0/4 apply-macro pfab'

set_cmd = 'set interfaces et-1/0/4 disable'
set_cmd = 'set interfaces et-1/0/8 disable'
set_cmd = 'set interfaces et-1/0/12 disable'
set_cmd = 'set interfaces et-1/0/16 disable'

#commit - Aug 27 04:38:40.737 - ras
set_cmd = 'delete interfaces xe-0/0/0:0 apply-macro wiring'
set_cmd = 'delete interfaces xe-0/0/0:1 disable'
set_cmd = 'delete interfaces xe-0/0/0:1 apply-macro pfab' 
set_cmd = 'set interfaces xe-0/0/0:1 description "NNI: Coresite OCX"'
set_cmd = 'delete interfaces xe-0/0/0:2 disable'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro wiring device_id 79' 
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro wiring market_id 34'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro wiring pop_id 186'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro wiring site_id 305'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro wiring reach 10km'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab customer_id 31'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab ifd_id 38'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab state avaliable'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab state assigned'
set_cmd = 'delete interfaces xe-0/0/0:2 description'
set_cmd = 'set interfaces xe-0/0/0:2 description "CUST: CoreSite | CKTID: PF-AP-LAX1-73 | IFD: 38"'
set_cmd = 'set interfaces xe-0/0/0:2 mtu 9096'
set_cmd = 'set interfaces xe-0/0/0:2 unit 0'
set_cmd = 'set interfaces xe-0/0/0:2 unit 0 apply-macro sflow'
set_cmd = 'set interfaces xe-0/0/0:2 unit 0 apply-macro pfab'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab ifl_id 17'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab neighbor 172.16.144.17'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab service l2circuit'
set_cmd = 'set interfaces xe-0/0/0:2 apply-macro pfab vc_id 1009'
set_cmd = 'set interfaces xe-0/0/0:2 unit 0 description IFL:17'
set_cmd = 'delete interfaces xe-0/0/0:3 disable'
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab customer_id 49'
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab state avaliable'
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab state assigned'
set_cmd = 'delete interfaces xe-0/0/0:3 description'
set_cmd = 'set interfaces xe-0/0/0:3 description "CUST: PacketFabric Demo | CKTID: PF-AP-LAX1-1119 | IFD: 359"'
set_cmd = 'set interfaces xe-0/0/0:3 interfaces xe-0/0/0:3 mtu 9096 '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '
set_cmd = 'set interfaces xe-0/0/0:3 apply-macro pfab '

#commit changes above
cu.load(set_cmd, format='set')

#This issues the commit. 
cu.commit()


#time between commits
#time.sleep(60)

#This closes the connection.  
dev.close()  

#If you have several boxes, just copy the above, changing the 


#Here is an example of adding something within the config 
#set_cmd = 'set logical-systems CE2 protocols msdp export reject_source2'

#Again, this loads the statement above to the box.  
#cu.load(set_cmd, format='set')