#utility to help capture exception packets 
#based off of Exceptions Debugging.docx 

#Scenario ->  Input DA rejects being seen, and you want to capture the packet to see what is causing it.  

#Example interface output: 
#
#@dis41-ottawa23_RE0> show interfaces et-7/1/0 extensive | match reject | refresh 10           
#Aug 26 13:18:19
#---(refreshed at 2017-08-26 13:18:19 EDT)---
#    Input packet rejects           19746341490
#    Input DA rejects               19744865858												<<< Packets that match my-mac check failed below 
#    Input SA rejects                         0

#Check jnh exceptions on the fpc, and you will see that this matches the my-mac check failed under Packet Exceptions 
#
#NPC7(dis41-ottawa23_RE0 vty)# show jnh 0 exceptions terse
#Reason                             Type         Packets      Bytes
#==================================================================
#
#
#PFE State Invalid
#----------------------
#invalid fabric token               DISC(75)       98668   27373561
#unknown iif                        DISC( 1)     1475632 1798494050
#egress pfe unspecified             DISC(19)       88710   58008941
#
#
#Packet Exceptions
#----------------------
#bad ipv4 hdr checksum              DISC( 2)      485454  506261370
#ttl expired                        PUNT( 1)   331823454 12020844569
#IP options                         PUNT( 2)       38173    4476100
#my-mac check failed                DISC(28)  19744865858 24098803206272					<<< Packets here 
#DDOS policer violation notifs      PUNT(15)         320      16640

#You may need to capture more/less agressively.  If so, here is where you can change it: (defaults to every 1000th packet - not good if a slow trickle of #traffic 
#
# test jnh exceptions-trace 

#NPC0(jtac-MX480-shared-r113-re0 vty)# test jnh exceptions-trace throttle    
#    <number>              value
#    default               value 1000
#    none                  log every packet



#The number you use in the next command in the number in () in the Type column above.  So for my-mac, we have DISC -> Discard and 28.  The following command can be used to capture it 

print "debug jnh exceptions x discard   <where x is the Type number.  You can change discard to punt if it is actually a punt instead of a discard>" 

#Now we enable capturing this packets and bringing them to the ukernel for review.  By default this function is disable.  We enable it here.  To disable, you do undebug instead of debug

print "debug jnh exceptions-trace" 

#Now view if packets are being captures 

print "show jnh exceptions-trace" 

#Example output 
#NPC0(jtac-MX480-shared-r113-re0 vty)# show jnh exceptions-trace
#[Aug 27 19:38:43.483] [156509] jnh_exception_packet_trace: ###############
#[Aug 27 19:38:43.483] [156510] jnh_exception_packet_trace: [iif:0,code/info:156 D(my-mac check failed)/0x0,score:tcp|(0x40),ptype:2/0,orig_ptype:2,offset:14,orig_offset:14,len:1196,l2iif:0,token=0]
#[Aug 27 19:38:43.483] [156511] jnh_exception_packet_trace: 0x00: 20 40 9c 00 00 00 00 00 00 0e 04 ac 80 00 00 20 
#[Aug 27 19:38:43.483] [156512] jnh_exception_packet_trace: 0x10: 0e 00 00 00 00 00 00 00 00 00 00 00 00 00 06 00 
#[Aug 27 19:38:43.483] [156513] jnh_exception_packet_trace: 0x20: 03 00 00 00 06 00 02 00 08 00 45 00 04 9e 00 00 
#[Aug 27 19:38:43.483] [156514] jnh_exception_packet_trace: 0x30: 00 00 40 06 70 55 02 02 02 02 01 01 01 01 00 00 
#[Aug 27 19:38:43.483] [156515] jnh_exception_packet_trace: 0x40: 00 00 00 00 00 00 00 00 00 00 50 00 00 00 38 c4 
#[Aug 27 19:38:43.483] [156516] jnh_exception_packet_trace: 0x50: 00 00 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 
#[Aug 27 19:38:43.484] [156517] jnh_exception_packet_trace: 0x60: 0e 0f 10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 
#[Aug 27 19:38:43.484] [156518] jnh_exception_packet_trace: 0x70: 1e 1f 20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 

#Now that we have verified we have got the packet, capture them for review off the box.  
#Now stop the debugging to return the box to normal 

print "undebug jnh exceptions x discard		<where x is the Type number.  You can change discard to punt if it is actually a punt instead of a discard>" 
print "undebug jnh exceptions-trace" 
 
#Now go to http://pester.jtac-emea.jnpr.net/decode_ukern_trace to decode into pcap - make sure to use the right version when decoding! 
 
#Test traffic being sent: 
# 
#destination mac 00 00 06 00 03 00
#source mac 00 00 06 00 02 00
#source ip 2.2.2.2
#destination ip 1.1.1.1

#Results of decode: 
#
#Packet(s):
#
#Download pcap
#Frame number: 0x1
#Frame 1: 0 bytes on wire (0 bits), 0 bytes captured (0 bits)
#[Malformed Packet: Ethernet]
#Frame number: 0x2
#Frame 2: 100 bytes on wire (800 bits), 100 bytes captured (800 bits)
#Ethernet II, Src: XeroxCor_00:02:00 (00:00:06:00:02:00), Dst: XeroxCor_00:03:00 (00:00:06:00:03:00)
#Internet Protocol Version 4, Src: 2.2.2.2, Dst: 1.1.1.1
#Transmission Control Protocol, Src Port: 0 (0), Dst Port: 0 (0), Seq: 1, Len: 46

#other potential useful outputs 

#NPC0(jtac-MX480-shared-r113-re0 vty)# show ukern_trace handles
#Ukernel Trace Info:
#ID     Name             Level     Printf Logging Size   Wrap 
#-----  ---------------  ---------  -----  -----  -----  -----
#0      Sched            terse      Off    On     65536      0
#1      Thread           terse      Off    Off        0      0
#2      JSNIFF           terse      Off    On     65536      0
#3      FPDL             terse      Off    On     65536      0
#4      FPB              terse      Off    On     65536      0
#5      IP               none       Off    Off        0      0
#6      wp3-pio          terse      Off    On     10000      0
#7      STATS            none       Off    Off        0      0
#8      blob             terse      Off    Off        0      0
#9      L2               terse      Off    On     65536      0
#10     TCAM             terse      Off    On     65536      0
#11     JNH              none       Off    Off        0      0
#12     JNH-EXCEPTIONS   none       Off    Off        0      0      << Can see that logging is off 

#Enable logging 

#NPC0(jtac-MX480-shared-r113-re0 vty)# debug jnh exceptions-trace     << Enables logging 

#NPC0(jtac-MX480-shared-r113-re0 vty)# show ukern_trace handles    
#Ukernel Trace Info:
#ID     Name             Level     Printf Logging Size   Wrap 
#-----  ---------------  ---------  -----  -----  -----  -----
#0      Sched            terse      Off    On     65536      0
#1      Thread           terse      Off    Off        0      0
#2      JSNIFF           terse      Off    On     65536      0
#3      FPDL             terse      Off    On     65536      0
#4      FPB              terse      Off    On     65536      0
#5      IP               none       Off    Off        0      0
#6      wp3-pio          terse      Off    On     10000      0
#7      STATS            none       Off    Off        0      0
#8      blob             terse      Off    Off        0      0
#9      L2               terse      Off    On     65536      0
#10     TCAM             terse      Off    On     65536      0
#11     JNH              none       Off    Off        0      0
#12     JNH-EXCEPTIONS   terse      Off    On     65536      0		<< Can now see logging is on (with ID 12) 

#Can view logging by by doing show the following and using the ID from above (or just do show jnh exceptions-trace

#NPC0(jtac-MX480-shared-r113-re0 vty)# show ukern_trace 12 
#[Aug 29 16:07:46.383] [273666] jnh_exception_packet_trace: ###############
#[Aug 29 16:07:46.383] [273667] jnh_exception_packet_trace: [iif:0,code/info:156 D(my-mac check failed)/0x0,score:tcp|(0x40),ptype:2/0,orig_ptype:2,offset:14,orig_offset:14,len:1196,l2iif:0,token=0]
#[Aug 29 16:07:46.383] [273668] jnh_exception_packet_trace: 0x00: 20 40 9c 00 00 00 00 00 00 0e 04 ac 80 00 00 20 
#[Aug 29 16:07:46.383] [273669] jnh_exception_packet_trace: 0x10: 0e 00 00 00 00 00 00 00 00 00 00 00 00 00 06 00 
#[Aug 29 16:07:46.383] [273670] jnh_exception_packet_trace: 0x20: 03 00 00 00 06 00 02 00 08 00 45 00 04 9e 00 00 
#[Aug 29 16:07:46.384] [273671] jnh_exception_packet_trace: 0x30: 00 00 40 06 70 55 02 02 02 02 01 01 01 01 00 00 
#[Aug 29 16:07:46.384] [273672] jnh_exception_packet_trace: 0x40: 00 00 00 00 00 00 00 00 00 00 50 00 00 00 38 c4 
#[Aug 29 16:07:46.384] [273673] jnh_exception_packet_trace: 0x50: 00 00 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 
#[Aug 29 16:07:46.384] [273674] jnh_exception_packet_trace: 0x60: 0e 0f 10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 
#[Aug 29 16:07:46.384] [273675] jnh_exception_packet_trace: 0x70: 1e 1f 20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 

 