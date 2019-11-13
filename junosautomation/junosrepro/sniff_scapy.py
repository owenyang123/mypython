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

subprocess.call(["ifconfig", "ens192", "promisc"], stdout = None, stderr = None, shell = False)

sniff(filter = "icmp and host 153.1.2.2", iface = "ens192", prn = lambda x: x.summary(), count = 30, timeout = 20)
