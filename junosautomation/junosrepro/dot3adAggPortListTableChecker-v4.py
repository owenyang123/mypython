#!/usr/bin/python


# File Name:
# dot3adAggPortListTableChecker-v4.py


# Written by:
# Jonathan A. Natale, BSEE, MSCS for Juniper Networks on 25-May.


# To Do:
#     Change (logically):
#         "has, in order"
#     to: 
#         "need not be contiguous, but
#         must be from the same router and have at least 1 instance (last instance is used) of each of:"
         
          
# Hisory:
# dot3adAggPortListTableChecker-v1.py - init
# dot3adAggPortListTableChecker-v2.py - simplified logic; fine-tuned help text
# dot3adAggPortListTableChecker-v3.py - work in progress
# dot3adAggPortListTableChecker-v3.py - removed version check, edited off-line (unix lost color :-( ), work in progress
# dot3adAggPortListTableChecker-v4.py - runs


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
    print "Each set of command captures has, in order:"
    print "    \"set cli timestamp"
    print "    \"set cli screen-length 0"
    print "    \"set cli screen-width 256"
    print "    \"show configuration | display set | match \"ae[0-9]+$\" | except demux"
    print "    \"show snmp mib walk ifDescr | match \" ([gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?)|ae[0-9]+) *$\""
    #print "    \"show snmp mib walk ifDescr | match \" [gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?) *$\""
    print "    \"show snmp mib walk dot3adAggPortListTable\""
    exit()


# Read input
fo = open(sys.argv[1])
cap = fo.read()
fo.close()


# a list of entries of:
#     " show BLAH"
#     ...
# -- SOOO... prompt/routerName from *previous* cmd is context for current cmd
cmds = cap.split(">")


rtr2aeDctViaCliDct = {}
rtr2aeDctViaSnmpDct = {}
rtr2ifIndexDctViaSnmpDct = {}


for cmd in cmds:

    # Get the CLI command that was entered, to be parsed with following if()s:
    indx = cmd.find("\n")
    
    
    if(cmd[:indx] == " show configuration | display set | match \"ae[0-9]+$\" | except demux"):
        # Logic Summary:
        #     rtr2aeDctViaCliDct & rtr2aeDctViaSnmpDct // init
        #         routerName         <<<< dict1 key    
        #         ae2mmbrLstDct      <<<< dict1 item   // create at show verson 
        #             ae#            <<<< dict2 key
        #             memberLst      <<<< dict2 item   // create at show config w/ ae
        #                 intfStr                      // add at show config w/ ge/xe
        # Example: rtr2aeDctViaCliDct[CMDNNJ-VFTTP-314][1][0] = "ge-0/0/0"  ---
        # z419512@CMDNNJ-VFTTP-314_RE0> show configuration | display set | match "ae[0-9]+$" | except demux
        # May 23 19:46:37
        # set interfaces ge-0/0/0 gigether-options 802.3ad ae1
        # set interfaces ge-0/0/1 gigether-options 802.3ad ae2
        # set interfaces ge-0/0/2 gigether-options 802.3ad ae3
        # 0123456789012345678901234567890123456789012345678901
        #           1         2         3         4         5


        # Get the file line
        lines = cmd[indx+1:].split('\n')[1:-3]


        for line in lines:
            # For Debugging:
            print "<%s>" % line

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
        # For debugging:
        #print "<%s>" % cmd[indx+1:]


        # Logic Summary:
        #     rtr2aeDctViaCliDct & rtr2aeDctViaSnmpDct
        #         routerName         <<<< dict1 key
        #         ae2mmbrLstDct      <<<< dict1 item
        #             ae#            <<<< dict2 key
        #             memberLst      <<<< dict2 item
        #                 intfStr
        # Example CLI output:
        # z419512@BSTNMA-VFTTP-331_RE0> show snmp mib walk ifDescr | match " ([gx]e-[0-9]+/[0-9]+/[0-9]+($|(\.(0|32767))?)|ae[0-9]+) *$"
        # Jun 10 13:32:37
        # ifDescr.574   = ge-0/0/0
        # ifDescr.575   = ge-0/0/1
        # ifDescr.576   = ge-0/0/2
        # ...
        # ifDescr.707   = ae0
        # ifDescr.708   = ae1
        # ifDescr.709   = ae2
        # ...
        # ifDescr.933   = xe-7/1/2.0
        # ifDescr.935   = xe-8/0/2.0
        # ifDescr.936   = xe-8/1/2.0
        # ifDescr.939   = xe-7/0/0.32767
        # ifDescr.941   = xe-8/0/0.32767
        # ifDescr.951   = ge-0/0/0.32767
        # 0123456789012345678901234567890123456789012345678901
        #           1         2         3         4         5


        lines = cmd[indx+1:].split('\n')[1:-3]
        for line in lines:
            # For Debugging:
            print "<%s>" % line


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
                print "ERROR: nullIfdescrIfindex--line=<%s>, routerName=<%s>, theIfIndex=<%s>, theMembers=<%s>\n" % (line, routerName, theIfIndex, theMembers)
    
    
    if(cmd[:indx] == " show snmp mib walk dot3adAggPortListTable"):
        # For debugging:
        #print "<%s>" % cmd[indx+1:]


        # Logic Summary:
        #     rtr2aeDctViaCliDct & rtr2aeDctViaSnmpDct
        #         routerName         <<<< dict1 key
        #         ae2mmbrLstDct      <<<< dict1 item
        #             ae#            <<<< dict2 key
        #             memberLst      <<<< dict2 item
        #                 intfStr
        # Example CLI output:
        # {master}
        # z419512@BSTNMA-VFTTP-331_RE0> show snmp mib walk dot3adAggPortListTable
        # Jun 10 13:32:45
        # dot3adAggPortListPorts.512 = 00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 0
        # 0 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 0
        # 0 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  0
        # 0 00 00 00  00 00 00 00  00 20
        # dot3adAggPortListPorts.540 = 00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 0
        # 0 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 0
        # 0 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  0
        # 0 00 00 00  00 00 00 00  00 10
        # dot3adAggPortListPorts.707 = 00
        # dot3adAggPortListPorts.708 =
        # dot3adAggPortListPorts.709
        # 0123456789012345678901234567890123456789012345678901
        #           1         2         3         4         5


        lines = cmd[indx+1:].split('\n')[1:-3]
        for line in lines:
            # For Debugging:
            print "<%s>" % line

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
                    print "NEW: line=<%s>, routerName=<%s>, theIfIndex=<%s>, theMembers=<%s>\n" % (line, routerName, theIfIndex, theMembers)
                else:
                    print "OLD: line=<%s>, routerName=<%s>, theIfIndex=<%s>, theMembers=<%s>\n" % (line, routerName, theIfIndex, theMembers)
                    rtr2aeDctViaSnmpDct[routerName][theIfIndex].append(theIntfStr)
            else:
                print "ERROR: nullDot3Ifindex--line=<%s>, routerName=<%s>, theIfIndex=<%s>, theMembers=<%s>\n" % (line, routerName, theIfIndex, theMembers)


    #if(cmd[:indx] == " show snmp mib walk dot3adAggPortListTable"):
 

    # get prompt from previous command; this is ok because "show version" is first cmd we care about but not first in cmd set.
    if(len(re.findall('@[^@]*$', cmd)) != 0):
        routerName = re.findall('@[^@]*$', cmd)[-1][1:]
        if(not routerName in rtr2aeDctViaCliDct):
            rtr2aeDctViaCliDct[routerName] = dict()
            rtr2ifIndexDctViaSnmpDct[routerName] = dict()
            rtr2aeDctViaSnmpDct[routerName] = dict()
        
        
# Check:
#TBD


exit()
