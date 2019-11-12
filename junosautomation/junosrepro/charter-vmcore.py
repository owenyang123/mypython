#Import Stuff
import time
import paramiko
import re
from pprint import pprint
import sys
import jnpr.junos
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
import lxml
from lxml import etree
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import LockError
from datetime import datetime
#Define variables for devices
#sunrise = Device (host='10.85.173.208',user='root',password='Juniper')
#svl = Device (host='10.85.173.211',user='labroot',password='lab123')
#Define Functions
#login() takes router variable as input and returns 0 if succesful, 1 if failed.
def login(router):
    try:
        router.open()
        return 0
    except ConnectError as err:
        print ("Cannot connect to device: {0}".format(err))
        return 1
#remshipstate() resturns 0 or 1 - whichever RE slot is master
def remshipstate(router):
    reinfo=router.rpc.get_route_engine_information()
    #print("Routing Engine in slot 0 is", reinfo.findtext("route-engine[slot='0']/mastership-state"))
    masterre=reinfo.findtext("route-engine[mastership-state='master']/slot")
    swinfo=router.rpc.get_software_information()
    sw='junos'
    if(masterre=='0'):
        sw=swinfo.findtext('package-information/comment')
    else:
        sw=swinfo.findtext('junos-version')
    print ("Routing Engine", masterre, "is currently master. Junos version =", sw)
    return masterre
#getcores() returns output
def getcores(router):
    coreinfo=router.rpc.get_system_core_dumps(normalize=True)
    cores=coreinfo.findtext("output")
    print("Core check:", cores)
    return cores
#getcores() returns output
def getuptime(router):
    timeinfo=router.rpc.get_system_uptime_information(normalize=True)
    uptime=timeinfo.findtext("uptime-information/up-time")
    print("Reston has been up for", uptime)
    uptimes=int(timeinfo.find("uptime-information/up-time").attrib['seconds'])
    return uptimes
def getroutesummary(router):
    routeinfo=router.rpc.get_route_summary_information()
    activeroutes=int(routeinfo.findtext('route-table/destination-count'))
    return activeroutes
def reswitchvoer(router):
    try:
        print("Initiating switchover and wait 90")
        pprint (router.cli("request chassis routing-engine master switch"))
        router.close()
    except:
        pass
    time.sleep(60)
def main():
    i=0
    reston = Device (host='10.85.173.151',user='root',password='Juniper')
    while (i<1000):
        login(reston)
        master=remshipstate(reston)
        if (master=='1'):
            aroutes=1
            while (aroutes<10000):
                print("Number of active routes =", aroutes,"are less than a 10000. WAIT 10")
                aroutes=getroutesummary(reston)
                time.sleep(50)
            print("Active Destinations=", aroutes)
            getcores(reston)
            timeup=getuptime(reston)
            if (timeup<7200):
                print("Routing Engine 1 was up less than 2 hrs, CODE=REPRO")
            str(datetime.now())
            reswitchvoer(reston)
        else:
            broutes=1
            while (broutes<10000):
                print("Number of active routes =", broutes,"are less than a 10000. WAIT 10")
                broutes=getroutesummary(reston)
                time.sleep(50)
            print("Active Destinations on RE0=", broutes)
            reswitchvoer(reston)
        i = i+1
        str(datetime.now())
        print ("[------------------------Iteration number:", i, "------------------------]")
if __name__ == "__main__":
    main()
