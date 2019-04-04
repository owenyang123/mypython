from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from lxml import etree
import re


for i in range(1,1000):
    dev=Device(host="10.85.174.57",user="labroot",password="lab123")
    dev.open()
    sw = dev.rpc.get_bridge_instance_information()
    rsp = dev.rpc.get_interface_information(terse=True)
    rsp1=dev.rpc.get_l2_learning_interface_information()
    t1=etree.tostring(sw)
    t2=etree.tostring(rsp)
    t3=etree.tostring(rsp1)
    dev.close()
    print t3
    print t2
    print t1
    print