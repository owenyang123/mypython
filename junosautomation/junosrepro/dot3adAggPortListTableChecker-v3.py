#!/usr/bin/python


# File Name:
# dot3adAggPortListTableChecker-v3.py


# Script Summary:
# The dot3adAggPortListTable value is an octet string, displayed as:
#     "xx xx xx xx  xx xx xx xx  xx xx xx xx  xx xx"
# for example (ending with 0, 1, 2, or 3 lone "xx"s, 2 in this example.)
#
# This script verifies the dot3adAggPortListTable for each set of command captures in the input file.
# Each set of command captures need not be contiguous, but
# must be from the same router and have at least 1 instance (last instance is used) of each of:
#     "show version"
#     "show configuration | display set | match "ae[0-9]+$" | except demux"
#     "show snmp mib walk ifDescr | match " [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$""
#     "show snmp mib walk dot3adAggPortListTable"


# Logic Summary:
#    fromCli & fromSnmp ea., get
#        routerName            <<<< dict1 key
#        listOfVerAndAes:      <<<< dict1 item
#            versionOnRouter
#            listOfAes:
#                ae             <<<< dict2 key
#                listOfMembers  <<<< dict2 item
#                    intf
#    check if cli == snmp


# Written by:
# Jonathan A. Natale, BSEE, MSCS for Juniper Networks on 25-May.


# Hisory:
# dot3adAggPortListTableChecker-v1.py - init
# dot3adAggPortListTableChecker-v2.py - simplified logic; fine-tuned help text
# dot3adAggPortListTableChecker-v3.py - work in progress


import sys
import re


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
routerName = "noneYet"
fromCli = {}
fromSnmp = {}
for cmd in cmds:
    indx = cmd.find("\n")
    if(cmd[:indx] == " show version"):
        # Get the version, which is between "#Junos: " and the next <CR>: 
        # For debugging:
        #print "Router %s has version %s" % (routerName, cmd[(cmd.find("Junos: ") + 7): (cmd.find("\n",cmd.find("Junos: ") + 7))])
        start = cmd.find("Junos: ") + 7
        endPlusOne = cmd.find("\n",cmd.find("Junos: ") + 7)
        version = cmd[start:endPlusOne]
        fromCli[routerName] = []
        fromSnmp[routerName] = []
        fromCli[routerName].append(version)
        fromSnmp[routerName].append(version)
        fromCli[routerName].append([])
        fromSnmp[routerName].append([])
        # For debugging:
        #print "~"
        #for router in fromCli:
        #    print "Router %s running version %s has AEs:" % (router, fromCli[router][0])
        #    for ae in fromCli[router][1]:
        #        printf("%s", ae)
        #print "~"
    if(cmd[:indx] == " show configuration | display set | match \"ae[0-9]+$\" | except demux"):
        print "<%s>" % cmd[indx+1:]
    if(cmd[:indx] == " show snmp mib walk ifDescr | match \" [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$\""):
        print "OK2"
    if(cmd[:indx] == " show snmp mib walk dot3adAggPortListTable"):
        print "OK3"
    if(len(re.findall('@[^@]*$', cmd)) != 0):
        routerName = re.findall('@[^@]*$', cmd)[-1][1:]


exit()
