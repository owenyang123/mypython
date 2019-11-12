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

target = '153.1.2.2'

ans, unans = sr(IP(dst = target ) / TCP(sport = RandShort(), dport = [111, 135, 22], flags = "S"), timeout = 5, iface = "ens192")

for sent, received in ans:
    if received.haslayer(TCP) and int(received[TCP].flags) == "18":
        print str(sent[TCP].dport) + " is OPEN!"
    elif received.haslayer(TCP) and int(received[TCP].flags) == "20":
        print str(sent[TCP].dport) + " is closed!"
    elif received.haslayer(ICMP) and int(received[ICMP].type) == "3":
        print str(sent[TCP].dport) + " is filtered!"

#Handling unanswered packets
for sent in unans:
    print int(sent[TCP].dport) + " is filtered!"


