#!/usr/bin/python


# File Name:
# dot3adAggPortListTableChecker-v2.py


# Summary:
# The dot3adAggPortListTable value is an octet string, displayed as:
#     "xx xx xx xx  xx xx xx xx  xx xx xx xx  xx xx"
# for example (ending with 0, 1, 2, or 3 lone "xx"s, 2 in this example.)
#
# This script verifies the dot3adAggPortListTable for each set of command captures in the input file.
# Each set of command captures need need not be contiguous, but
# must be from the same router and have at least 1 instance (last instance is used) of each of:
#     "show version"
#     "show configuration | display set | match "ae[0-9]+$" | except demux"
#     "show snmp mib walk ifDescr | match " [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$""
#     "show snmp mib walk dot3adAggPortListTable"


# Written by:
# Jonathan A. Natale, BSEE, MSCS for Juniper Networks on 25-May.


# Hisory:
# dot3adAggPortListTableChecker-v1.py - init
# dot3adAggPortListTableChecker-v2.py - simplified logic (work in progress)


import sys


if(len(sys.argv) != 2 or sys.argv[1][0].upper() == 'H' or sys.argv[1][0] == '?'):
    print "Usage:\n    %s <input file>\n\n" % sys.argv[0]
    print ""
    print "Summary:"
    print "The dot3adAggPortListTable value is an octet string comprised of hex chars, <x>, "
    print "displayed by the cli \"show snmp mib walk dot3adAggPortListTable.<ifIndexOfAe>\" as:"
    print "    \"00 00 00 00  00 00 00 00  00 00 00 00  00 80\""
    print "for example (ending with 0, 1, 2, or 3 lone \"<x><x>\"s, 2 in this example)."
    print "Each member of the ae is represented by a bit set to 1 for that member's ifIndex value."
    print "The bits are numbered left to right, starting with 1 (so in the example above, the ae has"
    print "a single member with an ifIndex of 205."
    print ""
    print "This script verifies the dot3adAggPortListTable (see above)"
    print "for each set of command captures in the input file."
    print "Each set of command captures need need not be contiguous, but"
    print "must be from the same router and have at least 1 instance (last instance is used) of each of:"
    print "    \"show version\""
    print "    \"show configuration | display set | match \"ae[0-9]+$\" | except demux\""
    print "    \"show snmp mib walk ifDescr | match \" [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$\"\""
    print "    \"show snmp mib walk dot3adAggPortListTable\""
    exit()


fo = open(sys.argv[1])
cap = fo.read()
fo.close()
cmds = cap.split(">")


cmdNum = 0
for cmd in cmds:
    indx = cmd.find("\n")
    if(cmd[:indx] == " show version"):
        print "OK0"
    if(cmd[:indx] == " show configuration | display set | match \"ae[0-9]+$\" | except demux"):
        print "OK1"
    if(cmd[:indx] == " show snmp mib walk ifDescr | match \" [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$\""):
        print "OK2"
    if(cmd[:indx] == " show snmp mib walk dot3adAggPortListTable"):
        print "OK3"


exit()
