#!/usr/bin/env python

import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
logging.getLogger("scapy.interactive").setLevel(logging.ERROR)
logging.getLogger("scapy.loading").setLevel(logging.ERROR)

try:
    from scapy.all import *
except ImportError:
    print("Scapy python loading error, please install SCAPY.")
    sys.exit()

target = ['10.85.184.135', '10.85.175.192', '153.1.2.2']

ans, unans = traceroute(target, minttl = 1, maxttl = 10, dport = [22, 23, 80], retry = 3, timeout = 1)
