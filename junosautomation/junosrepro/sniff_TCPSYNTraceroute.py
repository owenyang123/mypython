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

ans, unans = sr(IP(dst = target, ttl = (1, 5)) / TCP(dport = 53, flags = "S"), timeout = 5)

ans.summary(lambda(s, r): r.sprintf("%IP.src% --> ICMP:%ICMP.type% --> TCP:%TCP.flags%"))
