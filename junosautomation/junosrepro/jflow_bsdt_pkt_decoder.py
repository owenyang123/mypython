#!/usr/bin/env python
#
# Utility to decode export packet hexdump from jflow bsdt
#
# Author: Pankaj Malviya
#

import sys;
from struct import *;
import re;
import optparse;


#define some utility functions
def int2ipv4(i):
  return (str(i >> 24) + "." + str((i & 0xFF0000) >> 16) + "." + str((i & 0xFF00) >> 8) + "." + str(i & 0xFF));

def str2ipv6(s):
  ipbytes = unpack('!8H', s);
  ipv6str = '';
  for i in ipbytes:
    ipv6str += ':' + '%04x' % i;
  return ipv6str[1:];

def str2mac(s):
  macbytes = unpack('!6B', s);
  macstr = '';
  for i in macbytes:
    macstr += ':' + '%02x' % i;
  return macstr[1:];

def str2lbl(s):
  b = unpack('!HB', s);
  return str((b[0] << 4) + (b[1] >> 4)) + ', ' + str((b[1] >> 1) & 7) + ', ' + str(b[1] & 1);

empty_field_spec = ("NO FIELD", 'B', lambda x: str(x), 0);

class bsdtCflowTemplateDef173:
  # Packet Definition Tuples ("Description", "unpack specifier", "display function")
  ipv4_hdr_def = \
  [('Ver, header len', 'B', lambda x: str(x >> 4) + ", " + str((x & 0xF)<<2)),
   ('TOS', 'B', lambda x: str(x)),
   ('Total Len', 'H', lambda x: str(x)),
   ('Identification', 'H', lambda x: str(x)),
   ('Flag, Frag Offset', 'H', lambda x: str(x >> 5) + ", " + str(x & 0x1FFF)),
   ('TTL', 'B', lambda x: str(x)),
   ('Protocol', 'B', lambda x: str(x)),
   ('Header Checksum', 'H', lambda x: str(x)),
   ('Src IP', 'I', lambda x: int2ipv4(x)),
   ('Dst IP', 'I', lambda x: int2ipv4(x))
  ];
  
  ipv6_hdr_def = \
  [('Ver, Class, Flow Label', 'I', lambda x: str(x >> 28) + ', ' + hex((x >> 20) & 0xFF) + ', ' + hex(x & 0xFFFFF)),
   ('Len', 'H', lambda x: str(x)),
   ('Next Header', 'B', lambda x: str(x)),
   ('Hop Limit', 'B', lambda x: str(x)),
   ('Src IP', '16s', lambda x: str2ipv6(x)),
   ('Dst IP', '16s', lambda x: str2ipv6(x)),
  ];
  
  udp_hdr_def = \
  [('Src Port', 'H', lambda x: str(x)),
   ('Dst Port', 'H', lambda x: str(x)),
   ('Len', 'H', lambda x: str(x)),
   ('Checksum', 'H', lambda x: str(x))
  ];
  
  cflow_ipfix_hdr_def = \
  [('Cflow Version', 'H', lambda x: str(x)),
   ('Cflow Len', 'H', lambda x: str(x)),
   ('Timestamp', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('Flow Seq', 'I', lambda x: str(x)),
   ('Observation Domain ID', 'I', lambda x: str(x))
  ];
  
  cflow_v9_hdr_def = \
  [('Cflow Version', 'H', lambda x: str(x)),
   ('Count', 'H', lambda x: str(x)),
   ('Sys Uptime', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('UNIX Seconds', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('Sequence', 'I', lambda x: str(x)),
   ('Source ID', 'I', lambda x: str(x))
  ];
  
  cflow_flowset_hdr_def = \
  [('FLowset ID', 'H', lambda x: str(x)),
   ('Flowset Len', 'H', lambda x: str(x))
  ];
  
  ipv4_v9_flow_def = \
  [('SRC IP', 'I', lambda x: int2ipv4(x)),
   ('DST IP', 'I', lambda x: int2ipv4(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('ICMP TYPE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', 'I', lambda x: int2ipv4(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('IP Proto Ver', 'B', lambda x: str(x)),
   ('BGP Nexthop', 'I', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x))
  ];
  
  ipv4_ipfix_flow_def = \
  [('SRC IP', 'I', lambda x: int2ipv4(x)),
   ('DST IP', 'I', lambda x: int2ipv4(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('ICMP TYPE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', 'I', lambda x: int2ipv4(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('MIN TTL', 'B', lambda x: str(x)),
   ('MAX TTL', 'B', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   ('OUTER VLAN', 'H', lambda x: str(x)),
   ('INNER VLAN', 'H', lambda x: str(x)),
   ('FRAG ID', 'I', lambda x: str(x))
  ];
  
  ipv6_ipfix_flow_def = \
  [('SRC IP', '16s', lambda x: str2ipv6(x)),
   ('DST IP', '16s', lambda x: str2ipv6(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('TYPE CODE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', '16s', lambda x: str2ipv6(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('MIN TTL', 'B', lambda x: str(x)),
   ('MAX TTL', 'B', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   ('OUTER VLAN', 'H', lambda x: str(x)),
   ('INNER VLAN', 'H', lambda x: str(x)),
   ('IP IDENTIFIER', 'I', lambda x: str(x)),
   ('IP OPT HDR MASK', 'I', lambda x: str(x))
  ];
  
  ipv6_v9_flow_def = \
  [('SRC IP', '16s', lambda x: str2ipv6(x)),
   ('DST IP', '16s', lambda x: str2ipv6(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('TYPE CODE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', '16s', lambda x: str2ipv6(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   #('MIN TTL', 'B', lambda x: str(x)),
   #('MAX TTL', 'B', lambda x: str(x)),
   ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   #('FLOW END REASON', 'B', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   #('OUTER VLAN', 'H', lambda x: str(x)),
   #('INNER VLAN', 'H', lambda x: str(x)),
   #('IP IDENTIFIER', 'I', lambda x: str(x)),
   ('IP OPT HDR MASK', 'I', lambda x: str(x))
  ];
  
  vpls_ipfix_flow_def = \
  [('DST MAC', '6s', lambda x: str2mac(x)),
   ('SRC MAC', '6s', lambda x: str2mac(x)),
   ('ETH TYPE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('FLOW END REASON', 'B', lambda x: str(x))
  ];
  
  mpls_ipfix_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('FLOW END REASON', 'B', lambda x: str(x))
  ];
  
  mpls_ipv4_ipfix_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('TOP LABEL IP ADDR', 'I', lambda x: int2ipv4(x))
  ];
  mpls_ipv4_ipfix_flow_def.extend(ipv4_ipfix_flow_def);
  
  mpls_v9_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  mpls_ipv4_v9_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('TOP LABEL IP ADDR', 'I', lambda x: int2ipv4(x))
  ];
  mpls_ipv4_v9_flow_def.extend(ipv4_v9_flow_def);
  
  l3_hdr = \
  {'ipv4': ipv4_hdr_def,
   'ipv6': ipv6_hdr_def
  };
  
  cflow_hdr = \
  {'v9': cflow_v9_hdr_def,
   'ipfix': cflow_ipfix_hdr_def
  };
  
  flow_def = \
  {'v9':
   {'ipv4': ipv4_v9_flow_def,
    'ipv6' : ipv6_v9_flow_def,
    'mpls': mpls_v9_flow_def,
    'mpls-ipv4': mpls_ipv4_v9_flow_def
   },
   'ipfix':
   {'ipv4': ipv4_ipfix_flow_def,
    'ipv6': ipv6_ipfix_flow_def,
    'vpls': vpls_ipfix_flow_def,
    'mpls': mpls_ipfix_flow_def,
    'mpls-ipv4': mpls_ipv4_ipfix_flow_def
   }
  };

class bsdtCflowTemplateDef181:
  # Packet Definition Tuples ("Description", "unpack specifier", "display function")
  ipv4_hdr_def = \
  [('Ver, header len', 'B', lambda x: str(x >> 4) + ", " + str((x & 0xF)<<2)),
   ('TOS', 'B', lambda x: str(x)),
   ('Total Len', 'H', lambda x: str(x)),
   ('Identification', 'H', lambda x: str(x)),
   ('Flag, Frag Offset', 'H', lambda x: str(x >> 5) + ", " + str(x & 0x1FFF)),
   ('TTL', 'B', lambda x: str(x)),
   ('Protocol', 'B', lambda x: str(x)),
   ('Header Checksum', 'H', lambda x: str(x)),
   ('Src IP', 'I', lambda x: int2ipv4(x)),
   ('Dst IP', 'I', lambda x: int2ipv4(x))
  ];
  
  ipv6_hdr_def = \
  [('Ver, Class, Flow Label', 'I', lambda x: str(x >> 28) + ', ' + hex((x >> 20) & 0xFF) + ', ' + hex(x & 0xFFFFF)),
   ('Len', 'H', lambda x: str(x)),
   ('Next Header', 'B', lambda x: str(x)),
   ('Hop Limit', 'B', lambda x: str(x)),
   ('Src IP', '16s', lambda x: str2ipv6(x)),
   ('Dst IP', '16s', lambda x: str2ipv6(x)),
  ];
  
  udp_hdr_def = \
  [('Src Port', 'H', lambda x: str(x)),
   ('Dst Port', 'H', lambda x: str(x)),
   ('Len', 'H', lambda x: str(x)),
   ('Checksum', 'H', lambda x: str(x))
  ];
  
  cflow_ipfix_hdr_def = \
  [('Cflow Version', 'H', lambda x: str(x)),
   ('Cflow Len', 'H', lambda x: str(x)),
   ('Timestamp', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('Flow Seq', 'I', lambda x: str(x)),
   ('Observation Domain ID', 'I', lambda x: str(x))
  ];
  
  cflow_v9_hdr_def = \
  [('Cflow Version', 'H', lambda x: str(x)),
   ('Count', 'H', lambda x: str(x)),
   ('Sys Uptime', 'I', lambda x: str(x) + " " + str(x)),
   ('UNIX Seconds', 'I', lambda x: str(x) + " " + str(x)),
   ('Sequence', 'I', lambda x: str(x)),
   ('Source ID', 'I', lambda x: str(x))
  ];
  
  cflow_flowset_hdr_def = \
  [('FLowset ID', 'H', lambda x: str(x)),
   ('Flowset Len', 'H', lambda x: str(x))
  ];
  
  ipv4_v9_flow_def = \
  [('SRC IP', 'I', lambda x: int2ipv4(x)),
   ('DST IP', 'I', lambda x: int2ipv4(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('ICMP TYPE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', 'I', lambda x: int2ipv4(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('MIN TTL', 'B', lambda x: str(x)),
   ('MAX TTL', 'B', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('IP PROTO VER', 'B', lambda x: str(x)),
   ('BGP NEXTHOP', 'I', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   ('OUTER VLAN', 'H', lambda x: str(x)),
   ('INNER VLAN', 'H', lambda x: str(x)),
   ('FRAG ID', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  ipv4_ipfix_flow_def = \
  [('SRC IP', 'I', lambda x: int2ipv4(x)),
   ('DST IP', 'I', lambda x: int2ipv4(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('ICMP TYPE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', 'I', lambda x: int2ipv4(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('MIN TTL', 'B', lambda x: str(x)),
   ('MAX TTL', 'B', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('IP PROTO VER', 'B', lambda x: str(x)),
   ('BGP NEXTHOP', 'I', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   ('OUTER VLAN', 'H', lambda x: str(x)),
   ('INNER VLAN', 'H', lambda x: str(x)),
   ('FRAG ID', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  ipv6_ipfix_flow_def = \
  [('SRC IP', '16s', lambda x: str2ipv6(x)),
   ('DST IP', '16s', lambda x: str2ipv6(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('TYPE CODE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', '16s', lambda x: str2ipv6(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('MIN TTL', 'B', lambda x: str(x)),
   ('MAX TTL', 'B', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   ('OUTER VLAN', 'H', lambda x: str(x)),
   ('INNER VLAN', 'H', lambda x: str(x)),
   ('IP IDENTIFIER', 'I', lambda x: str(x)),
   ('IP OPT HDR MASK', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  ipv6_v9_flow_def = \
  [('SRC IP', '16s', lambda x: str2ipv6(x)),
   ('DST IP', '16s', lambda x: str2ipv6(x)),
   ('IP TOS', 'B', lambda x: str(x)),
   ('PROTOCOL', 'B', lambda x: str(x)),
   ('SRC PORT', 'H', lambda x: str(x)),
   ('DST PORT', 'H', lambda x: str(x)),
   ('TYPE CODE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('VLAN ID', 'H', lambda x: str(x)),
   ('SRC MASK', 'B', lambda x: str(x)),
   ('DST MASK', 'B', lambda x: str(x)),
   ('SRC AS', 'I', lambda x: str(x)),
   ('DST AS', 'I', lambda x: str(x)),
   ('NEXTHOP', '16s', lambda x: str2ipv6(x)),
   ('TCP FLAGS', 'B', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('MIN TTL', 'B', lambda x: str(x)),
   ('MAX TTL', 'B', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('FLOW DIRECTION', 'B', lambda x: str(x)),
   ('OUTER VLAN', 'H', lambda x: str(x)),
   ('INNER VLAN', 'H', lambda x: str(x)),
   ('IP IDENTIFIER', 'I', lambda x: str(x)),
   ('IP OPT HDR MASK', 'I', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  vpls_ipfix_flow_def = \
  [('DST MAC', '6s', lambda x: str2mac(x)),
   ('SRC MAC', '6s', lambda x: str2mac(x)),
   ('ETH TYPE', 'H', lambda x: str(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  mpls_ipfix_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  mpls_ipv4_ipfix_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('TOP LABEL IP ADDR', 'I', lambda x: int2ipv4(x))
  ];
  mpls_ipv4_ipfix_flow_def.extend(ipv4_ipfix_flow_def);
  
  mpls_v9_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('INPUT INT', 'I', lambda x: str(x)),
   ('OUTPUT INT', 'I', lambda x: str(x)),
   ('FLOW END REASON', 'B', lambda x: str(x)),
   ('OCTETS', 'Q', lambda x: str(x)),
   ('PACKETS', 'Q', lambda x: str(x)),
   ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
   ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]")
  ];
  
  mpls_ipv4_v9_flow_def = \
  [('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
   ('TOP LABEL IP ADDR', 'I', lambda x: int2ipv4(x))
  ];
  mpls_ipv4_v9_flow_def.extend(ipv4_v9_flow_def);
  
  l3_hdr = \
  {'ipv4': ipv4_hdr_def,
   'ipv6': ipv6_hdr_def
  };
  
  cflow_hdr = \
  {'v9': cflow_v9_hdr_def,
   'ipfix': cflow_ipfix_hdr_def
  };
  
  flow_def = \
  {'v9':
   {'ipv4': ipv4_v9_flow_def,
    'ipv6' : ipv6_v9_flow_def,
    'mpls': mpls_v9_flow_def,
    'mpls-ipv4': mpls_ipv4_v9_flow_def
   },
   'ipfix':
   {'ipv4': ipv4_ipfix_flow_def,
    'ipv6': ipv6_ipfix_flow_def,
    'vpls': vpls_ipfix_flow_def,
    'mpls': mpls_ipfix_flow_def,
    'mpls-ipv4': mpls_ipv4_ipfix_flow_def
   }
  };

# Packet Definition Tuples ("Description", "unpack specifier", "display function")
ipv4_hdr_def = \
[('Ver, header len', 'B', lambda x: str(x >> 4) + ", " + str((x & 0xF)<<2)),
 ('TOS', 'B', lambda x: str(x)),
 ('Total Len', 'H', lambda x: str(x)),
 ('Identification', 'H', lambda x: str(x)),
 ('Flag, Frag Offset', 'H', lambda x: str(x >> 5) + ", " + str(x & 0x1FFF)),
 ('TTL', 'B', lambda x: str(x)),
 ('Protocol', 'B', lambda x: str(x)),
 ('Header Checksum', 'H', lambda x: str(x)),
 ('Src IP', 'I', lambda x: int2ipv4(x)),
 ('Dst IP', 'I', lambda x: int2ipv4(x))
];

ipv6_hdr_def = \
[('Ver, Class, Flow Label', 'I', lambda x: str(x >> 28) + ', ' + hex((x >> 20) & 0xFF) + ', ' + hex(x & 0xFFFFF)),
 ('Len', 'H', lambda x: str(x)),
 ('Next Header', 'B', lambda x: str(x)),
 ('Hop Limit', 'B', lambda x: str(x)),
 ('Src IP', '16s', lambda x: str2ipv6(x)),
 ('Dst IP', '16s', lambda x: str2ipv6(x)),
];

udp_hdr_def = \
[('Src Port', 'H', lambda x: str(x)),
 ('Dst Port', 'H', lambda x: str(x)),
 ('Len', 'H', lambda x: str(x)),
 ('Checksum', 'H', lambda x: str(x))
];

cflow_ipfix_hdr_def = \
[('Cflow Version', 'H', lambda x: str(x)),
 ('Cflow Len', 'H', lambda x: str(x)),
 ('Timestamp', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
 ('Flow Seq', 'I', lambda x: str(x)),
 ('Observation Domain ID', 'I', lambda x: str(x))
];

cflow_v9_hdr_def = \
[('Cflow Version', 'H', lambda x: str(x)),
 ('Count', 'H', lambda x: str(x)),
 ('Sys Uptime', 'I', lambda x: str(x) + " " + str(x)),
 ('UNIX Seconds', 'I', lambda x: str(x) + " " + str(x)),
 ('Sequence', 'I', lambda x: str(x)),
 ('Source ID', 'I', lambda x: str(x))
];

cflow_flowset_hdr_def = \
[('FLowset ID', 'H', lambda x: str(x)),
 ('Flowset Len', 'H', lambda x: str(x))
];

ipv4_v9_flow_def = \
[('SRC IP', 'I', lambda x: int2ipv4(x)),
 ('DST IP', 'I', lambda x: int2ipv4(x)),
 ('IP TOS', 'B', lambda x: str(x)),
 ('PROTOCOL', 'B', lambda x: str(x)),
 ('SRC PORT', 'H', lambda x: str(x)),
 ('DST PORT', 'H', lambda x: str(x)),
 ('ICMP TYPE', 'H', lambda x: str(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('VLAN ID', 'H', lambda x: str(x)),
 ('SRC MASK', 'B', lambda x: str(x)),
 ('DST MASK', 'B', lambda x: str(x)),
 ('SRC AS', 'I', lambda x: str(x)),
 ('DST AS', 'I', lambda x: str(x)),
 ('NEXTHOP', 'I', lambda x: int2ipv4(x)),
 ('TCP FLAGS', 'B', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('MIN TTL', 'B', lambda x: str(x)),
 ('MAX TTL', 'B', lambda x: str(x)),
 ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
 ('FLOW END REASON', 'B', lambda x: str(x)),
 ('IP PROTO VER', 'B', lambda x: str(x)),
 ('BGP NEXTHOP', 'I', lambda x: str(x)),
 ('FLOW DIRECTION', 'B', lambda x: str(x)),
 ('OUTER VLAN', 'H', lambda x: str(x)),
 ('INNER VLAN', 'H', lambda x: str(x)),
 ('FRAG ID', 'I', lambda x: str(x))
];

ipv4_ipfix_flow_def = \
[('SRC IP', 'I', lambda x: int2ipv4(x)),
 ('DST IP', 'I', lambda x: int2ipv4(x)),
 ('IP TOS', 'B', lambda x: str(x)),
 ('PROTOCOL', 'B', lambda x: str(x)),
 ('SRC PORT', 'H', lambda x: str(x)),
 ('DST PORT', 'H', lambda x: str(x)),
 ('ICMP TYPE', 'H', lambda x: str(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('VLAN ID', 'H', lambda x: str(x)),
 ('SRC MASK', 'B', lambda x: str(x)),
 ('DST MASK', 'B', lambda x: str(x)),
 ('SRC AS', 'I', lambda x: str(x)),
 ('DST AS', 'I', lambda x: str(x)),
 ('NEXTHOP', 'I', lambda x: int2ipv4(x)),
 ('TCP FLAGS', 'B', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('MIN TTL', 'B', lambda x: str(x)),
 ('MAX TTL', 'B', lambda x: str(x)),
 ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('FLOW END REASON', 'B', lambda x: str(x)),
 ('IP PROTO VER', 'B', lambda x: str(x)),
 ('BGP NEXTHOP', 'I', lambda x: str(x)),
 ('FLOW DIRECTION', 'B', lambda x: str(x)),
 ('OUTER VLAN', 'H', lambda x: str(x)),
 ('INNER VLAN', 'H', lambda x: str(x)),
 ('FRAG ID', 'I', lambda x: str(x))
];

ipv6_ipfix_flow_def = \
[('SRC IP', '16s', lambda x: str2ipv6(x)),
 ('DST IP', '16s', lambda x: str2ipv6(x)),
 ('IP TOS', 'B', lambda x: str(x)),
 ('PROTOCOL', 'B', lambda x: str(x)),
 ('SRC PORT', 'H', lambda x: str(x)),
 ('DST PORT', 'H', lambda x: str(x)),
 ('TYPE CODE', 'H', lambda x: str(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('VLAN ID', 'H', lambda x: str(x)),
 ('SRC MASK', 'B', lambda x: str(x)),
 ('DST MASK', 'B', lambda x: str(x)),
 ('SRC AS', 'I', lambda x: str(x)),
 ('DST AS', 'I', lambda x: str(x)),
 ('NEXTHOP', '16s', lambda x: str2ipv6(x)),
 ('TCP FLAGS', 'B', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('MIN TTL', 'B', lambda x: str(x)),
 ('MAX TTL', 'B', lambda x: str(x)),
 ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('FLOW END REASON', 'B', lambda x: str(x)),
 ('FLOW DIRECTION', 'B', lambda x: str(x)),
 ('OUTER VLAN', 'H', lambda x: str(x)),
 ('INNER VLAN', 'H', lambda x: str(x)),
 ('IP IDENTIFIER', 'I', lambda x: str(x)),
 ('IP OPT HDR MASK', 'I', lambda x: str(x))
];

ipv6_v9_flow_def = \
[('SRC IP', '16s', lambda x: str2ipv6(x)),
 ('DST IP', '16s', lambda x: str2ipv6(x)),
 ('IP TOS', 'B', lambda x: str(x)),
 ('PROTOCOL', 'B', lambda x: str(x)),
 ('SRC PORT', 'H', lambda x: str(x)),
 ('DST PORT', 'H', lambda x: str(x)),
 ('TYPE CODE', 'H', lambda x: str(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('VLAN ID', 'H', lambda x: str(x)),
 ('SRC MASK', 'B', lambda x: str(x)),
 ('DST MASK', 'B', lambda x: str(x)),
 ('SRC AS', 'I', lambda x: str(x)),
 ('DST AS', 'I', lambda x: str(x)),
 ('NEXTHOP', '16s', lambda x: str2ipv6(x)),
 ('TCP FLAGS', 'B', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('MIN TTL', 'B', lambda x: str(x)),
 ('MAX TTL', 'B', lambda x: str(x)),
 ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
 ('FLOW END REASON', 'B', lambda x: str(x)),
 ('FLOW DIRECTION', 'B', lambda x: str(x)),
 ('OUTER VLAN', 'H', lambda x: str(x)),
 ('INNER VLAN', 'H', lambda x: str(x)),
 ('IP IDENTIFIER', 'I', lambda x: str(x)),
 ('IP OPT HDR MASK', 'I', lambda x: str(x))
];

vpls_ipfix_flow_def = \
[('DST MAC', '6s', lambda x: str2mac(x)),
 ('SRC MAC', '6s', lambda x: str2mac(x)),
 ('ETH TYPE', 'H', lambda x: str(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('FLOW END REASON', 'B', lambda x: str(x))
];

mpls_ipfix_flow_def = \
[('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('START TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'Q', lambda x: hex(x) + " [" + str(x) + "]"),
 ('FLOW END REASON', 'B', lambda x: str(x))
];

mpls_ipv4_ipfix_flow_def = \
[('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('TOP LABEL IP ADDR', 'I', lambda x: int2ipv4(x))
];
mpls_ipv4_ipfix_flow_def.extend(ipv4_ipfix_flow_def);

mpls_v9_flow_def = \
[('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('INPUT INT', 'I', lambda x: str(x)),
 ('OUTPUT INT', 'I', lambda x: str(x)),
 ('OCTETS', 'Q', lambda x: str(x)),
 ('PACKETS', 'Q', lambda x: str(x)),
 ('START TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
 ('END TIME', 'I', lambda x: hex(x) + " [" + str(x) + "]"),
];

mpls_ipv4_v9_flow_def = \
[('LABEL 0, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 1, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('LABEL 2, EXP, EOS', '3s', lambda x: str2lbl(x)),
 ('TOP LABEL IP ADDR', 'I', lambda x: int2ipv4(x))
];
mpls_ipv4_v9_flow_def.extend(ipv4_v9_flow_def);

l3_hdr = \
{'ipv4': ipv4_hdr_def,
 'ipv6': ipv6_hdr_def
};

cflow_hdr = \
{'v9': cflow_v9_hdr_def,
 'ipfix': cflow_ipfix_hdr_def
};

flow_def = \
{'v9':
 {'ipv4': ipv4_v9_flow_def,
  'ipv6' : ipv6_v9_flow_def,
  'mpls': mpls_v9_flow_def,
  'mpls-ipv4': mpls_ipv4_v9_flow_def
 },
 'ipfix':
 {'ipv4': ipv4_ipfix_flow_def,
  'ipv6': ipv6_ipfix_flow_def,
  'vpls': vpls_ipfix_flow_def,
  'mpls': mpls_ipfix_flow_def,
  'mpls-ipv4': mpls_ipv4_ipfix_flow_def
 }
};

# {"Test name": (l3proto, ver, family, numRecords)}
testParamsMap = \
{ "jflow, IPv4 flow export (Active Timeout)": ('ipv4', 'ipfix', 'ipv4', 1),
  "jflow, IPv4 flow export (Min/Max TTL)": ('ipv4', 'ipfix', 'ipv4', 1),
  'jflow, IPv4 flow export (Frag handling)': ('ipv4', 'ipfix', 'ipv4', 2),
  'jflow, IPv4 flow export (Inactive Timeout)': ('ipv4', 'ipfix', 'ipv4', 1),
  'jflow, IPv4 flow export (TCP FIN)': ('ipv4', 'ipfix', 'ipv4', 2),
  'jflow, IPv6 flow export (v6 tests)': ('ipv4', 'ipfix', 'ipv6', 7),
  'jflow, VPLS flow export (vpls tests)': ('ipv4', 'ipfix', 'vpls', 7),
  'jflow, IPv4 flow export (v9)': ('ipv6', 'v9', 'ipv4', 7),
  'jflow, MPLS flow export (mpls ipfix)': ('ipv4', 'ipfix', 'mpls', 7),
  'jflow, MPLS flow export (mpls v9)': ('ipv4', 'v9', 'mpls', 7),
  'jflow, MPLS-IPv4 flow export (mpls ipv4 v9)': ('ipv4', 'ipfix', 'mpls-ipv4', 7),
  'jflow, MPLS IPv4 flow export (mpls v9)': ('ipv4', 'v9', 'mpls-ipv4', 7),
  'jflow, IPv4 flow export (flow_dir/vlan key part)': ('ipv4', 'ipfix', 'ipv4', 7),
  'jflow, IPv6 flow export (flow_dir/vlan key part)': ('ipv4', 'ipfix', 'ipv6', 7),
  'jflow, MPLS-IPv4 flow export (flow_dir/vlan key part)': ('ipv4', 'ipfix', 'mpls-ipv4', 7),
  'jflow, IPv6 flow export (v6 v9 tests)': ('ipv4', 'v9', 'ipv6', 5),
  'jflow, nsb:  IPv4 flow export (Active Timeout)': ('ipv4', 'ipfix', 'ipv4', 7),
  'jflow, nsb:  IPv4 flow export (Min/Max TTL)': ('ipv4', 'ipfix', 'ipv4', 1),
  'jflow, nsb:  IPv4 flow export (Frag handling)': ('ipv4', 'ipfix', 'ipv4', 2),
  'jflow, nsb:  IPv4 flow export (Inactive Timeout)': ('ipv4', 'ipfix', 'ipv4', 1),
  'jflow, nsb:  IPv4 flow export (TCP FIN)': ('ipv4', 'ipfix', 'ipv4', 2),
  'jflow, nsb:  IPv6 flow export (v6 tests)': ('ipv4', 'ipfix', 'ipv6', 7),
  'jflow, nsb:  VPLS flow export (vpls tests)': ('ipv4', 'ipfix', 'vpls', 7),
  'jflow, nsb:  IPv4 flow export (v9)': ('ipv4', 'v9', 'ipv4', 7),
  'jflow, nsb:  MPLS flow export (mpls ipfix)': ('ipv4', 'ipfix', 'mpls', 7),
  'jflow, nsb:  MPLS flow export (mpls v9)': ('ipv4', 'v9', 'mpls', 7),
  'jflow, nsb:  MPLS-IPv4 flow export (mpls ipv4 v9)': ('ipv4', 'ipfix', 'mpls-ipv4', 7),
  'jflow, nsb:  MPLS IPv4 flow export (mpls v9)': ('ipv4', 'v9', 'mpls-ipv4', 7),
  'jflow, nsb:  IPv6 flow export (v6 v9 tests)': ('ipv4', 'v9', 'ipv6', 5),
  'jflow MPLSoGRE, IPv4 flow export (Active Timeout)':('ipv4', 'ipfix', 'ipv4', 7),
  'jflow MPLSoGRE, IPv4 flow export (Inactive Timeout)':('ipv4', 'ipfix', 'ipv4', 7),
  'nsb jflow MPLSoGRE, IPv4 flow export (Active Timeout)':('ipv4', 'ipfix', 'ipv4', 7),
  'nsb jflow MPLSoGRE, IPv4 flow export (Inactive Timeout)':('ipv4', 'ipfix', 'ipv4', 7),
  'jflow, IPv4 flow export (vbf pppoe)':('ipv4', 'ipfix', 'ipv4', 7),
  'jflow, IPv6 flow export (vbf pppoe)':('ipv4', 'ipfix', 'ipv6', 7)
};

def getTestParams(tpMap, testName):
  if tpMap.has_key(testName):
    return tpMap[testName];
  return None;

class lineParser:
  def __init__(self, tokenSpec):
    self.tokenSpec = tokenSpec;

  def tokenize(self, string):
    tokenRegex = re.compile('|'.join('(?P<%s>%s)' % pair for pair in self.tokenSpec));
    get_token = tokenRegex.match;
    tokens = [];
    for line in string.splitlines():
      token = get_token(line);
      #if token.lastgroup == 'testName' or token.lastgroup == 'parcelData':
      #  print token.lastgroup + "<>" + token.group(token.lastindex +1);
      #  print token.groups();
      #pos = token.end();
      #token = get_token(string, pos);
      tokens.append(token);
    return tokens;

class bsdtDiffParser:
  # tokenSpec: ("tokenType", "Regular expression for token")
  ts = [('testName', r'^\s*Test:\s*\"(.*)\"$'),
        ('parcelStart', r'^.*PType\s([a-zA-Z0-9]+)\s.*Channel.*$'),
        ('parcelData', r'^\s*([0-9a-fA-F]+)$'),
        ('parcelDataMinus', r'^\-\s*([0-9a-fA-F]+)$'),
        ('parcelDataPlus', r'^\+\s*([0-9a-fA-F]+)$'),
        ('ignore', r'.*')]; # ignore must always be at last
  
  stateDef = {"NONE": 0, "INIT": 1, "DONE": 2, "DATAMISS": (1<<7), "DATAEXTRA": (1 << 8)};
  tDef1 = bsdtCflowTemplateDef181();
  tDef2 = bsdtCflowTemplateDef181();

  def __init__(self, outputStr):
    self.parcelDef1 = [];
    self.parcelDef2 = [];
    self.pkt1Str = "";
    self.pkt2Str = "";
    self.testInfo = "";
    self.state = bsdtDiffParser.stateDef["NONE"];
    self.testName = "";
    self.inputData = outputStr;
    x = lineParser(bsdtDiffParser.ts);
    t = x.tokenize(self.inputData);
    for token in t:
      self.parseToken(token);

  def parseToken(self, token):
    # if we are already done collecting a parcel,
    # display it before parsing rest of the tokens
    if self.state & bsdtDiffParser.stateDef["DONE"]:
      self.show();
      self.state ^= bsdtDiffParser.stateDef["DONE"];
    fn = getattr(self, 'h' + token.lastgroup, None);
    if fn is not None:
      fn(token);
    else:
      raise Exception("ERROR: no handler to process token type \"%s\"" % token.lastgroup);

  def htestName(self, token):
    #self.state = bsdtDiffParser.stateDef["INIT"];
    # print the test name
    self.testName = token.group(token.lastindex + 1);
    # prepare the structure for decoding the parcel using the test name
    del self.parcelDef1[:];
    del self.parcelDef2[:];
    tp = getTestParams(testParamsMap, self.testName);
    #print tp;
    if tp is not None:
      self.appendPktDef1(self.tDef1.l3_hdr[tp[0]]);
      self.appendPktDef2(self.tDef2.l3_hdr[tp[0]]);
      self.appendPktDef1(self.tDef1.udp_hdr_def);
      self.appendPktDef2(self.tDef2.udp_hdr_def);
      self.appendPktDef1(self.tDef1.cflow_hdr[tp[1]]);
      self.appendPktDef2(self.tDef2.cflow_hdr[tp[1]]);
      self.appendPktDef1(self.tDef1.cflow_flowset_hdr_def);
      self.appendPktDef2(self.tDef2.cflow_flowset_hdr_def);
      recs = tp[3];
      while recs != 0:
        self.appendPktDef1(self.tDef1.flow_def[tp[1]][tp[2]]);
        self.appendPktDef2(self.tDef2.flow_def[tp[1]][tp[2]]);
        recs -= 1;

  def hignore(self, token):
    if self.state & bsdtDiffParser.stateDef["INIT"]:
      self.state |= bsdtDiffParser.stateDef["DONE"];
      self.state ^= bsdtDiffParser.stateDef["INIT"]; 

  def hparcelStart(self, token):
    self.pkt1Str = "";
    self.pkt2Str = "";
    self.state = bsdtDiffParser.stateDef["INIT"];

  def hparcelData(self, token):
    if self.state & bsdtDiffParser.stateDef["INIT"]:
      self.pkt1Str += token.group(token.lastindex + 1);
      self.pkt2Str += token.group(token.lastindex + 1);

  def hparcelDataMinus(self, token):
    self.state |= bsdtDiffParser.stateDef["DATAMISS"];
    if self.state & bsdtDiffParser.stateDef["INIT"]:
      self.pkt1Str += token.group(token.lastindex + 1);

  def hparcelDataPlus(self, token):
    self.state |= bsdtDiffParser.stateDef["DATAEXTRA"];
    if self.state & bsdtDiffParser.stateDef["INIT"]:
      self.pkt2Str += token.group(token.lastindex + 1);

  def appendPktDef1(self, defList):
    self.parcelDef1.append(defList);

  def appendPktDef2(self, defList):
    self.parcelDef2.append(defList);

  def decode(self, pktStr, pDef):
    res = [];
    start = 0;
    strLen = 0;
    pktLen = len(pktStr);
    for defItem in pDef:
      defStr = '!'; # for endianness
      for k, v, f in defItem:
        defStr += v;
      strLen = start + calcsize(defStr);
      if strLen > pktLen:
        print ("NOTICE: Remaining packet is %d bytes short of payload. Packet parsed correctly so far will only be displayed\n" % (strLen - pktLen));
        break;
      else:
        r = unpack(defStr, pktStr[start:strLen]);
        x = map(lambda pair: pair[0] + tuple([pair[1]]), zip(defItem, r));
        res.extend(x);
      start += calcsize(defStr);
    return res;

  def show(self):
    print "\nTest: %s" % self.testName;

    CSI="\x1B["
    reset=CSI+"m"

    if (self.state & bsdtDiffParser.stateDef["DATAEXTRA"]) and \
       (self.state & bsdtDiffParser.stateDef["DATAMISS"]):
      pkt1 = self.pkt1Str.decode("hex");
      pkt2 = self.pkt2Str.decode("hex");
      t1 = self.decode(pkt1, self.parcelDef1);
      t2 = self.decode(pkt2, self.parcelDef2);
      if len(t1) > len(t2):
        i = len(t1) - len(t2);
        while i > 0:
          t2.append(empty_field_spec);
          i -= 1;
      if len(t2) > len(t1):
        i = len(t2) - len(t1);
        while i > 0:
          t1.append(empty_field_spec);
          i -= 1;
      for pair in zip(t1, t2):
        if pair[0][3] != pair[1][3]:
          #print CSI + "1;31m" + '%-25s' % (pair[0][0] + ": ") + '%-15s' % pair[0][2](pair[0][3]) + '\t!= ' + '%-25s' % (pair[1][0] + ": ") + '%-15s' % pair[1][2](pair[1][3]) + CSI + "0m";
          print '%-25s' % (pair[0][0] + ": ") + '%-15s' % pair[0][2](pair[0][3]) + '\t!= ' + '%-25s' % (pair[1][0] + ": ") + '%-15s' % pair[1][2](pair[1][3]);
        else:
          print '%-25s' % (pair[0][0] + ": ") + '%-15s' % pair[0][2](pair[0][3]) + '\t== ' + '%-25s' % (pair[1][0] + ": ") + '%-15s' % pair[1][2](pair[1][3]);
    elif (self.state & bsdtDiffParser.stateDef["DATAMISS"]):
      pkt1 = self.pkt1Str.decode("hex");
      t1 = self.decode(pkt1, self.parcelDef1);
      print "Missing Parcel: %s" % self.pkt1Str;
      for a in t1:
        print '%-25s' % a[0] + " = " + a[2](a[3]);
    elif (self.state & bsdtDiffParser.stateDef["DATAEXTRA"]):
      print "Extra Parcel: %s" % self.pkt2Str;
      pkt1 = self.pkt2Str.decode("hex");
      t1 = self.decode(pkt1, self.parcelDef2);
      for a in t1:
        print '%-25s' % a[0] + " = " + a[2](a[3]);
    else:
      pkt1 = self.pkt2Str.decode("hex");
      t1 = self.decode(pkt1, self.parcelDef1);
      for a in t1:
        print '%-25s' % a[0] + " = " + a[2](a[3]);
    return;

class bsdtParcelDecoder:
  def __init__(self, parcelDef):
    self.parcelDef = [];
    self.parcelDef.append(parcelDef);
    self.showDiff = False;

  def appendPktDef(self, defList):
    self.parcelDef.append(defList);

  def prepStr(self):
    self.p1Str = "";
    self.p2Str = "";
    self.pktStr = "";
    self.testInfo = "";
    for line in sys.stdin:
      if re.match('\s*Test:', line) != None:
        self.testInfo = line;
      elif re.match('\+', line) != None:
        self.showDiff = True;
        line = re.sub('\+', '', line);
        self.p2Str += line;
      elif re.match('\-', line) !=None:
        self.showDiff = True;
        line = re.sub('\-', '', line);
        self.p1Str += line;
      else:
        self.p1Str += line;
        self.p2Str += line;

  def decode(self, pktStr):
    res = [];
    start = 0;
    strLen = 0;
    pktLen = len(pktStr);
    for defItem in self.parcelDef:
      defStr = '!';
      for k, v, f in defItem:
        defStr += v;
      strLen = start + calcsize(defStr);
      if strLen > pktLen:
        print ("Error: Remaning packet is %d bytes short of payload. Packet parsed correctly so far will be displayed\n" % (strLen - pktLen));
        break;
      else:
        r = unpack(defStr, pktStr[start:strLen]);
        x = map(lambda pair: pair[0] + tuple([pair[1]]), zip(defItem, r));
        res.extend(x);
      start += calcsize(defStr);
    return res;

  def show(self):
    CSI="\x1B["
    reset=CSI+"m"
    print self.testInfo;

    pkt1Str = re.sub('\s', '', self.p1Str);
    pkt1 = pkt1Str.decode("hex");
    t1 = self.decode(pkt1);
    if self.showDiff == True:
      pkt2Str = re.sub('\s', '', self.p2Str);
      pkt2 = pkt2Str.decode("hex");
      t2 = self.decode(pkt2);
      for pair in zip(t1, t2):
        if pair[0][3] != pair[1][3]:
          print CSI + "1;31m" + '%-25s' % (pair[0][0] + ": ") + '%-15s' % pair[0][2](pair[0][3]) + '\t!= ' + '%-25s' % (pair[1][0] + ": ") + '%-15s' % pair[1][2](pair[1][3]) + CSI + "0m";
        else:
          print '%-25s' % (pair[0][0] + ": ") + '%-15s' % pair[0][2](pair[0][3]) + '\t== ' + '%-25s' % (pair[1][0] + ": ") + '%-15s' % pair[1][2](pair[1][3]);
    else: 
      for a in t1:
        print '%-25s' % a[0] + " = " + a[2](a[3]);
    return;

usage = \
"""
%prog [options] <packet text>
    eg:
    cat simdiff.jflow.log | %prog

"""
parser = optparse.OptionParser(usage=usage);

options, args = parser.parse_args();

cflow_ver =  options.c;
l3proto =  options.n;
family = options.f;
recs = int(options.r);

simOp = "";
for line in sys.stdin:
  simOp += line;

# add extra empty tokens for safe parsing
simOp += "\n\n";
x=bsdtDiffParser(simOp);

