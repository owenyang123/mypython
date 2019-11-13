#!/usr/bin/python
# File Name: dot3adAggPortListTableChecker-v5.py
# Written by: Jonathan A. Natale, BSEE, MSCS for Juniper Networks on 25-May.
# dot3adAggPortListTableChecker-v1.py - init
# dot3adAggPortListTableChecker-v2.py - simplified logic; fine-tuned help text
# dot3adAggPortListTableChecker-v3.py - work in progress
# dot3adAggPortListTableChecker-v3.py - removed version check, edited off-line (unix lost color :-( ), work in progress
# dot3adAggPortListTableChecker-v4.py - runs
# dot3adAggPortListTableChecker-v5.py - work in progress
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
    print "a single member with an ifIndex of 105."
    print ""
    print "This script verifies the dot3adAggPortListTable (see above)"
    print "for each set of command captures in the input file."
    print "Each set of command captures is taken from the same router and has, in order:"
    print "    \"set cli timestamp"
    print "    \"set cli screen-length 0"
    print "    \"set cli screen-width 256"
    print "    \"show configuration | display set | match \"ae[0-9]+$\" | except demux"
    print "    \"show snmp mib walk ifDescr | match \" ([gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?)|ae[0-9]+) *$\""
    print "    \"show snmp mib walk dot3adAggPortListTable\""
    exit()
fo = open(sys.argv[1])
cap = fo.read()
fo.close()
cmds = cap.split(">")
rtr2aeDctViaCliDct = {}
rtr2aeDctViaSnmpDct = {}
rtr2ifIndexDctViaSnmpDct = {}
for cmd in cmds:
    indx = cmd.find("\n")
    if(cmd[:indx] == " show configuration | display set | match \"ae[0-9]+$\" | except demux"):
        lines = cmd[indx+1:].split('\n')[1:-3]
        for line in lines:
            start = line.find(" gigether-options 802.3ad ae") + 51
            endPlusOne = -1
            theAeNum = line[start:endPlusOne]
            start = line.find("set interfaces ") + 15
            endPlusOne = line.find(" gigether-options 802.3ad ae")
            theIntfStr = line[start:endPlusOne]
            if(not theAeNum in rtr2aeDctViaCliDct[routerName]):
                rtr2aeDctViaCliDct[routerName][theAeNum] = [theIntfStr]
            else:
                rtr2aeDctViaCliDct[routerName][theAeNum].append(theIntfStr)
    if(cmd[:indx] == " show snmp mib walk ifDescr | match \" ([gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?)|ae[0-9]+) *$\""):
        # ifDescr.951   = ge-0/0/0.32767
        # 01234567890123456
        #           1
        lines = cmd[indx+1:].split('\n')[1:-3]
        for line in lines:
            start = line.find("ifDescr.") + len("ifDescr.")
            beginOfStringOfSpacesAndEquals = re.search("[ =]+", line)
            if(beginOfStringOfSpacesAndEquals == None):
                theIfIndex = line[start:]
            else:
                endPlusOne = beginOfStringOfSpacesAndEquals.start()
                theIfIndex = line[start:endPlusOne]
            equalSign = line.find("=")
            if(equalSign == -1):
                theIntfStr = "missing="
            else:
                theIntfStr = line[start:]
            if(theIfIndex != ''):
                if(not theIfIndex in rtr2ifIndexDctViaSnmpDct[routerName]):
                    rtr2aeDctViaSnmpDct[routerName][theIfIndex] = [theIntfStr]
                else:
                    rtr2aeDctViaSnmpDct[routerName][theIfIndex].append(theIntfStr)
            else:
                print "ERROR:nullIfdescrIfindex-line=%s,routerName=%s,theIfIndex=%s,theMembers=%s\n" % \
                                                 (line,   routerName,   theIfIndex,  theMembers)
    if(cmd[:indx] == " show snmp mib walk dot3adAggPortListTable"):
        # dot3adAggPortListPorts.540 = 00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 10
        # dot3adAggPortListPorts.707 = 00
        # dot3adAggPortListPorts.708 =
        # dot3adAggPortListPorts.709
        # 0123456789012345678901234567890123456789012345678901
        #           1         2         3         4         5


        lines = cmd[indx+1:].split('\n')[1:-3]
        for line in lines:
            start = line.find("dot3adAggPortListPorts.") + len("dot3adAggPortListPorts.")
            beginOfStringOfSpacesAndEquals = re.search("[ =]+", line)
            if(beginOfStringOfSpacesAndEquals == None):
                theIfIndex = line[start:]
            else:
                endPlusOne = beginOfStringOfSpacesAndEquals.start()
                theIfIndex = line[start:endPlusOne]
            equalSign = line.find("=")
            if(equalSign == -1):
                theMembers = "missing="
            else:
                theMembers = line[equalSign+2:]
            if(theIfIndex != ''):
                if(not theIfIndex in rtr2ifIndexDctViaSnmpDct[routerName]):
                    rtr2ifIndexDctViaSnmpDct[routerName][theIfIndex] = [theMembers]
                    #print "NEW:line=%s,routerName=%s,theIfIndex=%s,theMembers=%s\n" % (line,routerName,theIfIndex,theMembers)
                else:
                    print "OLD:line=%s,routerName=%s,theIfIndex=%s,theMembers=%s\n" % (line,routerName,theIfIndex,theMembers)
                    rtr2aeDctViaSnmpDct[routerName][theIfIndex].append(theIntfStr)
            else:
                print "ERROR: nullDot3Ifindex--line=<%s>, routerName=<%s>, theIfIndex=<%s>, theMembers=<%s>\n" % (line, routerName, theIfIndex, theMembers)


    #if(cmd[:indx] == " show snmp mib walk dot3adAggPortListTable"):
 

    if(len(re.findall('@[^@]*$', cmd)) != 0):
        routerName = re.findall('@[^@]*$', cmd)[-1][1:]
        if(not routerName in rtr2aeDctViaCliDct):
            rtr2aeDctViaCliDct[routerName] = {}
            rtr2ifIndexDctViaSnmpDct[routerName] = {}
            rtr2aeDctViaSnmpDct[routerName] = {}
        
        
# Check:
#TBD


exit()
