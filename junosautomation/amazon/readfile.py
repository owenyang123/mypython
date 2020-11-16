from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.utils.start_shell import StartShell
import json
import os
import csv
import threading
with open('2020-07-13.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        print row
with open('2020-07-13.csv', 'r') as file:
    for row in file.readlines():
        if row:print row.replace("\n","").replace("\r","").split(',')