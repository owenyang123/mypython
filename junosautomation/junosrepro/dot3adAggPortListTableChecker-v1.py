#!/usr/bin/python


# File Name: dot3adAggPortListTableChecker-v1.py


# This script verifies the dot3adAggPortListTable for each set of commands in the input file.
# Each set of commands needs to be exactly captures of
# "show version",
# "show configuration | display set | match "ae[0-9]+$" | except demux",
# "show snmp mib walk ifDescr | match " [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$"", and
# "show snmp mib walk dot3adAggPortListTable", in that order.
# The dot3adAggPortListTable value is and octet string, displayed as
# xx xx xx xx  xx xx xx xx  xx xx xx xx  xx xx,
# for example (ending with 0, 1, 2, or 3 lone "xx"s, 2 in this example.)

# Written by Jonathan A. Natale, BSEE, MSCS for Juniper Networks on 25-May.


import sys


if(len(sys.argv) != 2):
    print "Usage:\n    %s <input file>\n\n" % sys.argv[0]
    exit()


fo = open(sys.argv[1])
cap = fo.read()
fo.close()
cmds = cap.split(">")


numOfCmds = 4
sanityCheck = []
sanityCheck.append(" show version")
sanityCheck.append(" show configuration | display set | match \"ae[0-9]+$\" | except demux")
sanityCheck.append(" show snmp mib walk ifDescr | match \" [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$\"")
sanityCheck.append(" show snmp mib walk dot3adAggPortListTable")
VERSION = 0
CONFIG = 1
IFDESCR = 2
DOT3AD = 3


cmdNum = 0
for cmd in cmds:
    if(cmd[:5] == " show"):
        indx = cmd.find("\n")
        if(cmd[:indx] != sanityCheck[cmdNum]):
           print "Input file %s missing \"%s\" #%d (got instead: \"%s\"), exiting..." % \
                  (sys.argv[1], sanityCheck[cmdNum],      cmdNum/numOfCmds,        cmd[:indx])
           exit()


        if(cmdNum == VERSION):
            print "OK0"


        #if(cmdNum == CONFIG):
            print "OK1"
            # TBD


        #if(cmdNum == IFDESCR):
            print "OK2"
            # TBD


        #if(cmdNum == DOT3AD):
            print "OK3"
            # TBD


        cmdNum = (cmdNum + 1) % numOfCmds


exit()
