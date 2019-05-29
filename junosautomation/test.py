from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from lxml import etree
import re


for i in range(1,1000):
    dev=Device(host="10.85.174.57",user="labroot",password="lab123")
    dev.open()
    sw = dev.rpc.get_bridge_instance_information()
    print sw
    t1=etree.tostring(sw)
    dev.close()
    print t1