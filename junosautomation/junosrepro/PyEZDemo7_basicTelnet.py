#!/usr/local/bin/python2.7


# File:  PyEZDemo7_basicTelnet.py
# Author:  Jonathan A. Natale
# Date:  2-Sep-2016
# Synopsis:  Demos PyEZ


from jnpr.junos import Device
import sys
from pprint import pprint
from getpass import getpass
import telnetlib
import time

passwordEntered = getpass('Enter password: ')

time.sleep(3)

# Notes: wait for prompt and then time.sleep, else you might over-flow input
tn = telnetlib.Telnet('172.19.163.192')
tn.read_until("login: ")
time.sleep(3)

tn.write('labroot' + "\n")
tn.read_until("Password:", 50)
time.sleep(3)

tn.write((passwordEntered + "\n")
tn.read_until("> ", 50)
time.sleep(3)

tn.write(("show system uptime" + "\n")
tn.read_until("> ", 50)
time.sleep(3)

tn.write(("exit" + "\n")
print tn.read_all()

