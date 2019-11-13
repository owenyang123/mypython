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

target = '8.8.8.8'

ans, unans = sr(IP(dst = target, ttl = (1,10)) / UDP() / DNS(qd = DNSQR(qname = "google.com")), timeout = 5)

ans.summary(lambda(s,r) : r.sprintf("%IP.src%"))
