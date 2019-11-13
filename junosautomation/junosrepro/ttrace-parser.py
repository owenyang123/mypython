'''
Created on Nov 16, 2016

@author: ktanish
'''
import os
import re
import time
import sys
import string
import codecs
from httplib import FOUND


#dict1 = {handle_wan :0 ,handle_fab :1 ,handle_host :2}
from_WAN_regex = re.compile("(^[0-9]+\s+handle_wan.*)")
iif_regex=re.compile("(^.*SetIIFNH.*:iif.*)")
KTLeaf_regex=re.compile("(^[0-9]+\s+KTLeaf_terminat.*)")
pfeDest_regex=re.compile("(^.*pfeDest:.*)")
gpr31_regex=re.compile("(^[0-9]?\s+GPR31.*)")



from_FAB_regex = re.compile("(^[0-9]+\s+handle_fabric.*)")
ueid_regex = re.compile("(^.*ueid.*)")
oif_regex = re.compile("(^.*entry_set_oif_nh.*)")
xrs_regex = re.compile("(^\s+xrs:.*)")
lag_regex = re.compile("(.*SetIIFNH.*\s$)")

from_HOST_regex = re.compile("(^[0-9]+\s+handle_host.*)")
terminate_regex = re.compile("(^[0-9]+\s+send_pkt_terminate_if_all_done.*)")

exception = {  0    :'DISC(0)      frame format error                     ',
            1    :'DISC(1)      unknown iif                            ',
            2    :'DISC(2)      bad ipv4 hdr checksum                  ',
            3    :'DISC(3)      iif STP blocked                        ',
            4    :'DISC(4)      non-IPv4 layer3 tunnel                 ',
            5    :'DISC(5)      GRE unsupported flags                  ',
            6    :'DISC(6)      tunnel pkt too short                   ',
            7    :'DISC(7)      tunnel format error                    ',
            8    :'DISC(8)      mcast rpf mismatch                     ',
            9    :'DISC(9)      bad IPv6 options pkt                   ',
            10    :'DISC(10)     invalid loopback pkt format            ',
            11    :'DISC(11)     bad IPv4 hdr                           ',
            12    :'DISC(12)     bad IPv4 pkt len                       ',
            13    :'DISC(13)     L4 len too short                       ',
            14    :'DISC(14)     invalid TCP fragment                   ',
            15    :'DISC(15)     dmac miss                              ',
            16    :'DISC(16)     tcam miss                              ',
            17    :'DISC(17)     mac learn limit exceeded               ',
            18    :'DISC(18)     static mac on unexpected iif           ',
            19    :'DISC(19)     egress pfe unspecified                 ',
            20    :'DISC(20)     no local switching                     ',
            21    :'DISC(21)     mtu exceeded                           ',
            24    :'DISC(24)     mcast smac on bridged iif              ',
            26    :'DISC(26)     bridge ucast split horizon             ',
            27    :'DISC(27)     MRRU exceeeded                         ',
            28    :'DISC(28)     my-mac check failed                    ',
            29    :'DISC(29)     pppoe hdr error                        ',
            30    :'DISC(30)     pppoe pkt len error                    ',
            31    :'DISC(31)     oif STP blocked                        ',
            32    :'DISC(32)     vlan id out of oif\'s range             ',
            33    :'DISC(33)     mcast stack overflow                   ',
            34    :'DISC(34)     invalid ml frag state                  ',
            35    :'DISC(35)     sample stack error                     ',
            36    :'DISC(36)     undefined nexthop opcode               ',
            37    :'DISC(37)     internal ucode error                   ',
            38    :'DISC(38)     frame relay type unsupported           ',
            41    :'DISC(41)     invalid fabric hdr version             ',
            42    :'DISC(42)     virtual-chassis error                  ',
            43    :'DISC(43)     bad CLNP hdr                           ',
            44    :'DISC(44)     bad CLNP hdr checksum                  ',
            45    :'DISC(45)     incorrect length in GTP header         ',
            46    :'DISC(46)     GTP header errors                      ',
            47    :'DISC(47)     unknown ktree prefix                   ',
            48    :'DISC(48)     ppp session unknown                    ',
            49    :'DISC(49)     vbf lookup failed                      ',
            50    :'DISC(50)     dv discard                             ',
            51    :'DISC(51)     dv no ctrl ifl                         ',
            52    :'DISC(52)     non vbf gre                            ',
            63    :'DISC(63)     my-mac check failed IPv6               ',
            64    :'DISC(64)     sw error                               ',
            65    :'DISC(65)     debug                                  ',
            66    :'DISC(66)     discard route                          ',
            67    :'DISC(67)     firewall discard                       ',
            69    :'DISC(69)     access security violation              ',
            70    :'DISC(70)     hold route                             ',
            72    :'DISC(72)     invalid stream                         ',
            73    :'DISC(73)     unknown family                         ',
            75    :'DISC(75)     invalid fabric token                   ',
            76    :'DISC(76)     GRE key mismatch                       ',
            77    :'DISC(77)     unknown vrf                            ',
            78    :'DISC(78)     mac firewall                           ',
            79    :'DISC(79)     pppoe session unknown                  ',
            80    :'DISC(80)     pppoe session down                     ',
            81    :'DISC(81)     pppoe session mac mismatch             ',
            82    :'DISC(82)     ppp proto unconfigured                 ',
            83    :'DISC(83)     ppp proto down                         ',
            84    :'DISC(84)     lt unknown ucast                       ',
            85    :'DISC(85)     Expected drops                         ',
            86    :'DISC(86)     invalid L2 token                       ',
            87    :'DISC(87)     iif down                               ',
            88    :'DISC(88)     mc lag color                           ',
            89    :'DISC(89)     directed bcast                         ',
            90    :'DISC(90)     invalid inline-svcs state              ',
            91    :'DISC(91)     input trunk vlan lookup failed         ',
            92    :'DISC(92)     output trunk vlan lookup failed        ',
            93    :'DISC(93)     nh id out of range                     ',
            94    :'DISC(94)     LSI/VT vlan validation failed          ',
            95    :'DISC(95)     Mcast iif list check failed            ',
            96    :'DISC(96)     dsc ifl discard route                  ',
            97    :'DISC(97)     invalid encap                          ',
            98    :'DISC(98)     invalid outgoing paths/interfaces      ',
            99    :'DISC(99)     mac validate                           ',
            100    :'DISC(100)    invalid vNode MX-DCF state             ',
            101    :'DISC(101)    firewall discard V6                    ',
            102    :'DISC(102)    discard route IPv6                     ',
            103    :'DISC(103)    link layer bcast inet check            ',
            104    :'DISC(104)    vbf li discard                         ',
            108    :'DISC(108)    ppp pkt lcp hdr len error              ',
            109    :'DISC(109)    iif start jnh is not found             ',
            110    :'DISC(110)    bad IPv6 hdr                           ',
            111    :'DISC(111)    bad IPv6 pkt len                       ',
            112    :'DISC(112)    GTPc packets with msg-type TPDU are discarded',    
            113    :'DISC(113)    firewall discard out                   ',
            114    :'DISC(114)    firewall discard V6 out                ',
            115    :'DISC(115)    invalid bundle entry                   ',
            116    :'DISC(116)    divide by 0                            ',
            117    :'DISC(117)    unknown src mac                        ',
            118    :'DISC(118)    destination cchip to qsys mismatch     ',
            119    :'DISC(119)    Incorrect vxlan fw path executed       ',
            120    :'DISC(120)    mpls perf monitor error                ',
            121    :'DISC(121)    PVLAN violation                        ',
            122    :'DISC(122)    access security V6 violation           ',
            124    :'DISC(124)    invalid pfe alive version              ',
            125    :'DISC(125)    mlp pkt                                ',
            127    :'DISC(127)    Non-DF state, valid discard            ',
            }

punt = { 1    :'PUNT(1)      ttl expired                       ', 
         2    :'PUNT(2)      IP options                        ', 
         3    :'PUNT(3)      ICMP redirect                     ', 
         4    :'PUNT(4)      control pkt punt via ucode        ', 
         5    :'PUNT(5)      fab probe                         ', 
         6    :'PUNT(6)      mcast host copy                   ', 
         7    :'PUNT(7)      bridge pkt punt                   ', 
         8    :'PUNT(8)      tunnel hdr needs reassembly       ', 
         11    :'PUNT(11)     mlp pkt                           ', 
         12    :'PUNT(12)     IGMP snooping control packet      ', 
         13    :'PUNT(13)     virtual-chassis ttl error         ', 
         14    :'PUNT(14)     xlated l2pt                       ', 
         15    :'PUNT(15)     DDOS policer violation notifs     ', 
         17    :'PUNT(17)     lu notification                   ', 
         18    :'PUNT(18)     PIM snooping control packet       ', 
         19    :'PUNT(19)     MLD snooping control packet       ', 
         20    :'PUNT(20)     mpls perf monitor                 ', 
         32    :'PUNT(32)     host route                        ', 
         33    :'PUNT(33)     resolve route                     ', 
         34    :'PUNT(34)     control pkt punt via nh           ', 
         35    :'PUNT(35)     dynamic-vlan auto-sense           ', 
         36    :'PUNT(36)     firewall reject                   ', 
         38    :'PUNT(38)     services pkt internal test        ', 
         39    :'PUNT(39)     IP-demux auto-sense               ', 
         40    :'PUNT(40)     reject route                      ', 
         41    :'PUNT(41)     sample syslog                     ', 
         42    :'PUNT(42)     sample host                       ', 
         43    :'PUNT(43)     sample pfe                        ', 
         44    :'PUNT(44)     sample tap                        ', 
         45    :'PUNT(45)     pppoe padi pkt                    ', 
         46    :'PUNT(46)     pppoe padr pkt                    ', 
         47    :'PUNT(47)     pppoe padt pkt                    ', 
         48    :'PUNT(48)     ppp lcp pkt                       ', 
         49    :'PUNT(49)     ppp auth pkt                      ', 
         50    :'PUNT(50)     ppp IPv4cp                        ', 
         51    :'PUNT(51)     ppp IPv6cp                        ', 
         52    :'PUNT(52)     ppp MPLScp                        ', 
         53    :'PUNT(53)     ppp unclassified cp               ', 
         54    :'PUNT(54)     firewall send to host             ', 
         55    :'PUNT(55)     virtual-chassis pkt(hi)           ', 
         56    :'PUNT(56)     virtual-chassis pkt(lo)           ', 
         57    :'PUNT(57)     ppp ISIS                          ', 
         58    :'PUNT(58)     Tunnel keepalives                 ', 
         59    :'PUNT(59)     firewall send to Inline-services  ', 
         60    :'PUNT(60)     ppp lcp echo request pkt          ', 
         61    :'PUNT(61)     Inline KA control                 ', 
         63    :'PUNT(63)     ppp lcp echo reply pkt            ', 
         64    :'PUNT(64)     mlppp lcp pkt                     ', 
         65    :'PUNT(65)     mlfr control pkt                  ', 
         66    :'PUNT(66)     mfr control pkt                   ', 
         68    :'PUNT(68)     reject route V6                   ', 
         69    :'PUNT(69)     resolve route V6                  ', 
         70    :'PUNT(70)     services pkt                      ', 
         71    :'PUNT(71)     sample sflow                      ', 
         73    :'PUNT(73)     captive portal IPv4               ', 
         74    :'PUNT(74)     captive portal IPv6               ', 
         75    :'PUNT(75)     l2tp                              ', 
         76    :'PUNT(76)     dhcp server                       ', 
         77    :'PUNT(77)     vbf gre                           ', 
         78    :'PUNT(78)     vbf resolve                       ',  } 

                   
trace2 =[]
from_wan = []
from_fab = []
from_host = []
from_gpr31 = []
from_xrs = []
counter1 = 0
counter2 = 0
from_terminate = []
iif =[]
pfedest=[]

def from_WAN(result190 , item1 ,item ,list2 = []):
    count = 0
    from_wan.append(result190)
    for item4,item5 in enumerate(list2[item1+1:trace2_len]):
        z = re.match(iif_regex ,item5)
        if z :
            j = item5
            from_wan.append(item5)
            iif.append(j.split(':')[2].split(',')[0])
            continue
        y = re.match(pfeDest_regex ,item5)
        if y :
            k = item5
            from_wan.append(item5)
            pfedest.append(k.split(',')[0])
            pfedest.append(k.split(',')[2])
            continue
        x = re.match(gpr31_regex ,item5)
        if x :
            from_gpr31.append(item5)
            continue 
        p = re.match(terminate_regex ,item5)
        if p :
            from_terminate.append(item5)
            from_terminate.append(list2[item1+item4+4])
            continue
    #print from_wan
    #line = from_wan[1].split(',')[0].split(':')[2]
    try:
        for l in iif:
            print "The incomming IFL and interface is  " + l
        print "\n"
    except:
        print "There is no incomming interface mentioned or found  in the trace"
    try:
        print "Destination pfe and fabric token are below :- "
        print "Note :- More destination PFEs, the outgoing interface can be a LAG or if empty there will be no destinaton pfe "
        for m in pfedest :
            print m
        print "\n"
    except :
        print "There is no Destination PFE mentioned in the Trace"
        print "\n"

    termlen = len(from_terminate)
    #print termlen
    if termlen :
        #print "\n"
        #print "from send_packet_terminate" + from_terminate[termlen - 1]
        line4 = from_terminate[termlen - 1][-3:]
        packet_terminate_fun = int(line4 ,16)
        #print packet_terminate_fun
        if packet_terminate_fun > 0 and packet_terminate_fun < 1008:
            fpc = packet_terminate_fun/4
            pfe = packet_terminate_fun%4
            print "The packet forwarded to fpc %d pfe %d "  %(fpc,pfe) 
            print "\n"
        elif packet_terminate_fun == 0 :
            print "The packet has encountered a drop"
            print "\n"
        else:
            print "The packet is punted to Host,HostQ " +str(packet_terminate_fun)
            print "\n"
    
    else:
        print "Packet terminate function not found "
        exit()
        #print "\n"
    
    gpr31len = len(from_gpr31)
    if gpr31len :
         #print "from GPR31 : " + from_gpr31[gpr31len-1]
         line1 = from_gpr31[gpr31len-1].split(' ')[-1]
         line2 = line1[6:8]
         #print line2
         line3 = int(line2 , 16)
         #print line3
         if line3 >= 128 :
             result = line3 -128
             if packet_terminate_fun >= 1008 :
                 print "Punt reason fron the punt table is " + punt[result]
                 print "\n"
             else :
                 print "Exception reason from the exception table is " + exception[result]
         elif (line3 == 0 ) :
            print "The packet is forwarded to destination PFE through Fabric and fabric Q %s " %(packet_terminate_fun)
            print "\n"
         else :
            #print line3
            if packet_terminate_fun >= 1008 :
                 print "Punt reason fron the punt table is " + punt[line3]
                 print "\n"
            else :
                 #print exception[line3]
                 print "Exception reason from the table   is --- > " + exception[line3]
                 print "\n"
    else :
        print "Script is not able to find GPR31 to check for exception !!!!!!!!"
  
    return

def from_FAB(result200 , item1 ,item ,list2 = []):
    from_fab.append(result200)
    for item4 ,item5 in enumerate(list2[item1+1:trace2_len]):
        z = re.match(ueid_regex ,item5)
        if z :
            from_fab.append(item5)
            continue
        y = re.match(oif_regex ,item5) 
        if y :
            from_fab.append(item5)
            for item6 in list2[item1+item4:item1+item4+6]:
                #print item6
                x = re.match(xrs_regex ,item6)
                if x :
                    from_xrs.append(item6)
                    break
        w = re.match(gpr31_regex ,item5)
        if w :
            from_gpr31.append(item5)
            continue 
        p = re.match(terminate_regex ,item5)
        if p :
            from_terminate.append(item5)
            from_terminate.append(list2[item1+item4+4])
            continue
            #break
    
    #print from_fab
    
    #line = from_fab[1].split(',')[2][:-1]
    line = from_fab[1].split(' ')[-1][:-1]
    #print "\nThe fabric ueid is " +  line.split(' ')[2]
    print "\nThe fabric ueid is " +  line
    #print "\n"
    
    line1 = from_xrs[-1].split(' ')[-1]
    print "Use show jnh decode on %s to deode the destination \n" %line1 
    #print from_xrs
    
    termlen = len(from_terminate)
    #print termlen
    if termlen :
        #print "\n"
        #print "from send_packet_terminate" + from_terminate[termlen - 1]
        line4 = from_terminate[termlen - 1][-3:]
        packet_terminate_fun = int(line4 ,16)
        #print packet_terminate_fun
        if packet_terminate_fun > 0 and packet_terminate_fun < 128:
            #fpc = packet_terminate_fun/4
            #pfe = packet_terminate_fun%4
            print "The packet forwarded to wanQ %d \n"  %(packet_terminate_fun) 
            print "\n"
        elif packet_terminate_fun >= 128 and packet_terminate_fun < 1008 :
            packet_terminate_fun = packet_terminate_fun - 128
            print "The packet forwarded to wanQ %d \n"  %(packet_terminate_fun)
        elif packet_terminate_fun == 0 :
            print "The packet has encountered a drop"
            print "\n"
        else:
            print "The packet is punted to Host,HostQ " +str(packet_terminate_fun)
            print "\n"
    
    else:
        print "Packet terminate function not found "
        exit()
        #print "\n"
    
    gpr31len = len(from_gpr31)
    if gpr31len :
         #print "from GPR31 : " + from_gpr31[gpr31len-1]
         line3 = from_gpr31[gpr31len-1].split(' ')[-1]
         line4 = line3[6:8]
         #print line4
         line5 = int(line4 , 16)
         #print line5
         if line5 >= 128 :
             result = line5 -128
             if packet_terminate_fun >= 1008 :
                 print "Punt reason fron the punt table is " + punt[result]
                 print "\n"
             else :
                 print "Exception reason from the exception table is " + exception[result]
         elif (line5 == 0 ) :
            print "The packet is forwarded to destination PFE , WAN Q %s " %(packet_terminate_fun)
            print "\n"
         else :
            #print line3
            if packet_terminate_fun >= 1008 :
                 print "Punt reason fron the punt table is " + punt[line5]
                 print "\n"
            else :
                 #print exception[line3]
                 print "Exception reason from the table   is --- > " + exception[line5]
                 print "\n"
    else :
        print "Script is not able to find GPR31 to check for exception !!!!!!!!"
    return 

def from_HOST(result210 , item1 ,item ,list2 = []):
    from_host.append(result210)
    for item4 ,item5 in enumerate(list2[item1+1:trace2_len]):
        z = re.match(terminate_regex ,item5)
        if z :
            from_terminate.append(item5)
            from_terminate.append(list2[item1+item4+4])
            continue
            #break
        w = re.match(gpr31_regex ,item5)
        if w :
            from_gpr31.append(item5)
            continue
        
   # print from_host
    termlen = len(from_terminate)
    #print termlen
    if termlen :
        #print "\n"
        #print "from send_packet_terminate" + from_terminate[termlen - 1]
        line4 = from_terminate[termlen - 1][-3:]
        packet_terminate_fun = int(line4 ,16)
        #print packet_terminate_fun
        if packet_terminate_fun > 0 and packet_terminate_fun < 1008:
            fpc = packet_terminate_fun/4
            pfe = packet_terminate_fun%4
            print "The packet forwarded to fpc %d pfe %d "  %(fpc,pfe) 
            print "\n"
        elif packet_terminate_fun == 0 :
            print "The packet has encountered a drop"
            print "\n"
        else:
            print "The packet is punted to Host,HostQ " +str(packet_terminate_fun)
            print "\n"
    
    else:
        print "Packet terminate function not found "
        exit()
        #print "\n"
    
    gpr31len = len(from_gpr31)
    if gpr31len :
         #print "from GPR31 : " + from_gpr31[gpr31len-1]
         line1 = from_gpr31[gpr31len-1].split(' ')[-1]
         line2 = line1[6:8]
         #print line2
         line3 = int(line2 , 16)
         #print line3
         if line3 >= 128 :
             result = line3 -128
             if packet_terminate_fun >= 1008 :
                 print "Punt reason fron the punt table is " + punt[result]
                 print "\n"
             else :
                 print "Exception reason from the exception table is " + exception[result]
         elif (line3 == 0 ) :
            print "The packet is forwarded to destination PFE through Fabric and fabric Q %s " %(packet_terminate_fun)
            print "\n"
         else :
            #print line3
            if packet_terminate_fun >= 1008 :
                 print "Punt reason fron the punt table is " + punt[line3]
                 print "\n"
            else :
                 #print exception[line3]
                 print "Exception reason from the table   is --- > " + exception[line3]
                 print "\n"
    else :
        print "Script is not able to find GPR31 to check for exception !!!!!!!!"
  
    return
    return

try:
 path=sys.argv[1]
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/from_host.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/ttrace-transit-packet-egress.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/ttrace-transit-packet-ingress.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/ttrace-packet-firewallDrop.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/ttrace-packet-toLoopback.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/ttrace-packet-ttl1.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/test.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/complete-ttrace.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/ttrace-mpls-fwfilter.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/nitin-ttrace-1.txt'
 #path = 'C:/Users/ktanish/Desktop/ttrace-project/nitin-ttrace-2.txt'
 trace1 = open(path ,'U')
except:
     print "Kindly verify the path, not able to open " + path
     exit()
     
list1 = trace1.read()
trace2 = list1.split("\n")
#print trace2
trace2_len=len(trace2)
#print  trace2_len

for item1,item in enumerate(trace2):
    result = re.findall(from_WAN_regex , str(item))
    if result:
        counter1 = counter1 + 1
        if counter1 == 1 :
            print "The packet is from WAN PORT "
            from_WAN(result,item1,item,trace2)
            #continue
            exit()
    result = re.findall(from_FAB_regex , str(item))
    if result:
        counter2 = counter2 + 1
        if counter2 == 1:
            print " This packet is from Fabric "
            from_FAB(result,item1,item,trace2)
            #continue
            exit()
    result = re.findall(from_HOST_regex , str(item))
    if result:
        print "This packet is from the host "
        from_HOST(result,item1,item,trace2)
        exit()

print "Sorry ,ttrace is not in the supported format !!!!!!!!!!!!"

