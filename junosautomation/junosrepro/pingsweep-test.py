'''This script is to execute the shell level commands in an infinite loop. How to run the script# from a Ubuntu server running python3 
$ python3 --version
Python 3.4.3
$python3 <.pyfilename>'''
import os
'''
A simple python program to see if the devices in the text file a pingable or not
servers.txt contains ip address in following format
10.85.100.52
10.85.47.70
'''
with open('servers.txt', 'r') as f:
        for ip in f:
            result=os.system("ping -c 1 " + ip)
            if result==0:
                print(ip, "active")
            else:
                print(ip, "inactive")