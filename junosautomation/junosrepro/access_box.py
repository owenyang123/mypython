#!/usr/bin/python
import sys
import time 
import datetime
from pprint import pprint  
from jnpr.junos import Device
import csv

dev = Device(host='10.85.174.57', user='labroot', password='lab123')
dev.open()  
data = dev.facts
pprint(data)
dev.close()

with open('namemodel.csv','wb') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)

    filewriter.writerow(['Name', 'Model'])





