'''This script is to execute the shell level commands in an infinite loop. How to run the script# from a Ubuntu server running python3 
$ python3 --version
Python 3.4.3
$python3 <.pyfilename>, the script makes use of PYEZ juniper library'''
#!/usr/bin/env python3
'''This script is to execute the shell level commands'''
import time
from jnpr.junos.utils.start_shell import StartShell
from jnpr.junos import Device
dev = Device(host='x.x.x.x',user='labroot',password='lab123')
dev.open()
with StartShell(dev) as shell:
        i=0
        while i<1: 
                threads=shell.run('cprod -A fpc0 -c "show threads cpu"')
                print ("at {} threads command". format(time.asctime()))
                for lines in threads:
                        print(lines)
                time.sleep(2)
dev.close()        
