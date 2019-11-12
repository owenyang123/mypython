automation@automation:~$ vim PyEZDemo1.py

from jnpr.junos import Device import sys

dev = Device(host="dc1a.example.com", user="username", passwd="password")
try:
    dev.open()
except Exception as err:
    print err
    sys.exit(1)

print dev.facts

dev.close()
