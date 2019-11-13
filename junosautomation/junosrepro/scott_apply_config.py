import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors

#set system services netconf ssh must be enabled, or it will error out 


#dev contains the box you want to open and the credentials 
dev = Device(host='NAME OF ROUTER HERE', user='labroot', password='lab123')
dev.open()

#Start config mode 
cu = Config(dev)

#Here is an example of deleting something within the config - just give the full set command 
set_cmd = 'delete logical-systems CE2 protocols msdp export reject_source1'

#this line is needed after the set command to actually apply it to the box 
cu.load(set_cmd, format='set')

#Here is an example of adding something within the config 
set_cmd = 'set logical-systems CE2 protocols msdp export reject_source2'

#Again, this loads the statement above to the box.  
cu.load(set_cmd, format='set')

#This issues the commit. 
cu.commit()

#This closes the connection.  
dev.close()  

#If you have several boxes, just copy the above, changing the 