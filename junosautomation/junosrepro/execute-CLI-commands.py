'''This script is to execute the CLI level commands in an infinite loop. How to run the script# from a Ubuntu server running python3 
$ python3 --version
Python 3.4.3
$python3 <.pyfilename> '''
#!/usr/bin/env python3
#import time and device modules, 
import time
from jnpr.junos import Device
dev = Device(host='x.x.x.x',user='labroot',password='lab123')
dev.open()
i=0
while i<1: 
        ddos=dev.cli("show ddos-protection protocols statistics terse")
        print ("at {} ddos command". format(time.asctime()))
        print(ddos)
        time.sleep(2)
        ''' NEXT COMMAND '''
        system_process=dev.cli("show system processes extensive | no-more")
        print ("at {} system_process command". format(time.asctime()))
        print(system_process)
        time.sleep(2)
        ''' NEXT COMMAND '''
        DHCP_relay=dev.cli("show dhcp relay statistics")
        print ("at {} DHCP_relay command". format(time.asctime()))
        print(DHCP_relay)
        time.sleep(2)
        ''' NEXT shell COMMAND '''
        threads=dev.cli("start shell command")
        print ("at {} threads command". format(time.asctime()))
        print(threads)
        time.sleep(2)
dev.close()        

