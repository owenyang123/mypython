from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from lxml import etree
import re


dev=Device(host="10.85.174.179",user="labroot",password="lab123")
dev.open()
sw = dev.rpc.get_software_information()
rsp = dev.rpc.get_interface_information(terse=True)
t1=etree.tostring(sw)
t2=etree.tostring(rsp)
dev.close()
print t1
print t2