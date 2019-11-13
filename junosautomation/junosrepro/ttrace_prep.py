#0d0d0d01 - 13.13.13.1 in hex 

#Based off of Packet_Capture_Tracing_MX_PTX.pptx

pfe_value = raw_input('Enter pfe number: ')
match_value = raw_input('Enter match pattern: ')
offset_value = raw_input('Enter offset value (enter default 16 unless you need to capture more in incrments of 16): ')

#disable background noise 
print "Run these before doing ttrace:\n"
print "test jnh %s pfe-liveness stop" % (pfe_value)
print "test fabric self_ping disable %s" % (pfe_value)
print "set host_loopback disable-periodic\n\n" 

#start packet capture
print "Packet capture part\n" 
print "test jnh %s packet-via-dmem enable 64000" % (pfe_value)     									#64000 here is the capture size 
print "test jnh %s packet-via-dmem capture 0x3 %s %s" % (pfe_value, match_value, offset_value) 	   	#0x3 is both packet types below: 
																									#m2l_packet (0x1) - less than 128/256/192 bye packet, so complete packet 
																									#m2l_pkt_head (0x2) - just first 128/256/192 bytes (just the head of the packet)
																									#for more on offset, see PG 22 of Packet_Capture_Tracing_MX_PTX.pptx
print "test jnh %s packet-via-dmem capture 0x0"	% (pfe_value) 										#stopping the capture

#time to dump the packet we just captured
print "test jnh %s packet-via-dmem dump\n"% (pfe_value) 
print "\n\nCOPY EVERYTHING HERE, but only INJECT everything after the RECEIVED dispatch cookie\n\n"

############  EXAMPLE CAPTURE OF 13.13.13.1
#NPC2(owsley-re0 vty)# test jnh 0 packet-via-dmem dump
#PFE 0 LKUP_INST 0 Parcel Dump:
#
#Wallclock: 0x30a842b4					<<<<<<<<<<<<<<<<<<< Copy from here when using the decode parcels page: http://10.219.49.145/ttrace/index.php
#Received 126 byte parcel:
#Dispatch cookie: 0x007e000000000000
#0x07 0x80 0x47 0xf0 0x80 0x00 0x00 0x00 <<<<<<<<<<<<<<<<<< This is what we will need to inject 
#0x00 0x00 0x00 0x01 0x00 0x00 0x82 0x00 
#0x03 0x00 0x00 0x00 0x00 0x00 0xbe 0xad 
#0x83 0x55 0x80 0x71 0x1f 0x82 0x82 0x95 
#0x08 0x00 0x45 0x00 0x00 0x54 0xf8 0xdc 
#0x00 0x00 0x40 0x01 0x4d 0xb0 0x0d 0x0d 
#0x0d 0x02 0x0d 0x0d 0x0d 0x01 0x08 0x00 
#0x28 0x13 0xf4 0x1c 0x0a 0x6c 0x59 0x21 
#0xfd 0x92 0x00 0x01 0x8f 0xab 0x08 0x09 
#0x0a 0x0b 0x0c 0x0d 0x0e 0x0f 0x10 0x11 
#0x12 0x13 0x14 0x15 0x16 0x17 0x18 0x19 
#0x1a 0x1b 0x1c 0x1d 0x1e 0x1f 0x20 0x21 
#0x22 0x23 0x24 0x25 0x26 0x27 0x28 0x29 
#0x2a 0x2b 0x2c 0x2d 0x2e 0x2f 0x30 0x31 
#0x32 0x33 0x34 0x35 0x36 0x37 
#Wallclock: 0x30a849cc
#Sent 111 byte parcel:
#0xd8 0xbf 0xef 0x00 0x10 0x00 0x00 0x08 
#0xc0 0x00 0x00 0x80 0xfa 0x00 0x00 0xbe 
#0xad 0x83 0x55 0x80 0x71 0x1f 0x82 0x82 
#0x95 0x08 0x00 0x45 0x00 0x00 0x54 0xf8 
#0xdc 0x00 0x00 0x40 0x01 0x4d 0xb0 0x0d 
#0x0d 0x0d 0x02 0x0d 0x0d 0x0d 0x01 0x08 
#0x00 0x28 0x13 0xf4 0x1c 0x0a 0x6c 0x59 
#0x21 0xfd 0x92 0x00 0x01 0x8f 0xab 0x08 
#0x09 0x0a 0x0b 0x0c 0x0d 0x0e 0x0f 0x10 
#0x11 0x12 0x13 0x14 0x15 0x16 0x17 0x18 
#0x19 0x1a 0x1b 0x1c 0x1d 0x1e 0x1f 0x20 
#0x21 0x22 0x23 0x24 0x25 0x26 0x27 0x28 
#0x29 0x2a 0x2b 0x2c 0x2d 0x2e 0x2f 0x30 
#0x31 0x32 0x33 0x34 0x35 0x36 0x37 

#Time for ttrace 
print "test jnh %s packet-via-dmem inject trace\n" % (pfe_value)

######## TTRACE OUTPUT 
#NPC2(owsley-re0 vty)# test jnh 0 packet-via-dmem inject trace    
#Please paste hex dump of the packet, end with a dot (.)
#0x07 0x80 0x47 0xf0 0x80 0x00 0x00 0x00
#0x00 0x00 0x00 0x01 0x00 0x00 0x82 0x00
#0x03 0x00 0x00 0x00 0x00 0x00 0xbe 0xad
#0x83 0x55 0x80 0x71 0x1f 0x82 0x82 0x95
#0x08 0x00 0x45 0x00 0x00 0x54 0xf8 0xdc
#0x00 0x00 0x40 0x01 0x4d 0xb0 0x0d 0x0d
#0x0d 0x02 0x0d 0x0d 0x0d 0x01 0x08 0x00
#0x28 0x13 0xf4 0x1c 0x0a 0x6c 0x59 0x21
#0xfd 0x92 0x00 0x01 0x8f 0xab 0x08 0x09
#0x0a 0x0b 0x0c 0x0d 0x0e 0x0f 0x10 0x11
#0x12 0x13 0x14 0x15 0x16 0x17 0x18 0x19
#0x1a 0x1b 0x1c 0x1d 0x1e 0x1f 0x20 0x21
#0x22 0x23 0x24 0x25 0x26 0x27 0x28 0x29
#0x2a 0x2b 0x2c 0x2d 0x2e 0x2f 0x30 0x31
#0x32 0x33 0x34 0x35 0x36 0x37 
#.
#[May 21 20:54:36.448 LOG: Info] TTRACE PPE12 Context4 now in-active.
#Version 17.1-20170511.0 by builder on 2017-05-11 01:16:14 UTC
#
#
#0  parcel_copy_finished @ 0x6503 (pending hw_trap_base @ 0x0000)
#    GPR00-GPR31:
#GPR00-03:  0xe3ff000000000000 802081d800000000 1800000000300000 0010e80000000000
#GPR04-07:  0x0000000000e014ee 0000000800000000 a6d5c700414947d0 0026882dadd00000
#GPR08-11:  0x0000000000000000 0000000000000000 0709cb2000200020 ffffff0000000000
#GPR12-15:  0x0000000000000000 0000000000000000 003f020003000000 f25b261798406e73
#GPR16-19:  0x0000000000000000 0000000000000000 3fff23fc00000000 0000000000000000
#GPR20-23:  0x00708c98004062a7 a6d5ecb041494739 0000000000000000 0000000000000000
#GPR24-27:  0x0000000000000000 0000000000000000 0000000000000000 10b0108167000010
#GPR28-31:  0x0000000000000008 0000000000000000 0000000000000000 0000000000000000
#    tstatus0:  Prev_PC 0x6503 VA_3 - VA_0 0xc00 000 000 000
#    tstatus1:  NH2_cmdsz: 2 NH2_Trap: 0x0048, PCSD: 0
#               Priv LMEM Addr 0x1e, PPE 12, Context 4
#        wp64:  WP3 - WP0 0x0000 0000 0f80 0000
#        xrs:  0x323334353637beef
#        xra:  0x0000000000000000
#       ir64:  IR1 0x00000000  IR0 0x001a5751
#LM_CACHE_CTRL:  0x0000100b 0x00001008 0x00001009 0x0000100a
#                0x00001009 0x00001008 0x0000100b 0x0000100a
#               
#CALL_STACK: 
#LMEM (byte offsets) -- LU complex 0 PPE12_CNTX4 bound to zone 30:
#LMEM 000  0x0000000080000010 8000001206b01081 67fe8282e7800000 00000000022688ff
#LMEM 020  0xfe2dadd03a88002a 0000000000000000 0000000000000000 007e000000000000
#LMEM 040  0x000047f080000000 0000000100008200 030000000000bead 835580711f828295
#LMEM 060  0x080045000054f8dc 000040014db00d0d 0d020d0d0d010800 2813f41c0a6c5921
#LMEM 080  0xfd9200018fab0809 0a0b0c0d0e0f1011 1213141516171819 1a1b1c1d1e1f2021
#LMEM 0a0  0x2223242526272829 2a2b2c2d2e2f3031 323334353637beef 0000000000050000
#LMEM 0c0  0x0000000000000005 0000000000000000 0000000000000000 0000000000000000
#LMEM 0e0  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 100  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 120  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 140  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 160  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 180  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 1a0  0x0000000000000000 0000000000000000 0000000000000000 00d08a6480107003
#LMEM 1c0  0xf11a002200000001 d0bfe68011900080 2000000100010001 d0bfff4008000000
#LMEM 1e0  0x0000000000000000 0000000000000000 2048000000000001 10b0108167000028
#LMEM 200  0x00000018000000ff 0001000000000000 0000000000000000 0000000000000000
#LMEM 220  0xfe03600000000000 0000000400000000 c000d12e00000000 000000000080812c
#LMEM 240  0x01a6ef0001a66f00 000080000001adfb 2779851c00000000 0000000000000000
#LMEM 260  0x000000008a0803aa 4000000801000000 1100000000000000 0000000000000000
#LMEM 280  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 2a0  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 2c0  0x3900000000000000 0000000000000000 0000000000002000 00068030b2000000
#LMEM 2e0  0x0000000000000000 0000000000000000 00000000c000d9e0 c000d900c000d982
#LMEM 300  0xc000d910c000d992 c000d920c000d9a2 c000da18c000d9b2 800000cb00000000
#LMEM 320  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 340  0x000000027798c815 8303e03fe0001000 03f21c000b000000 00000000001d0000
#LMEM 360  0x00000000000000d5 55a20cc3d7732500 0000000000000000 0723000000000000
#LMEM 380  0x840000000000c040 0000000000000000 0000000000000000 0000000000000000
#LMEM 3a0  0x0000000000000000 0000000000000000 0000000000000000 0000000000000000
#LMEM 3c0  0x00708c980040ffe1 20886ed90001dda1 408871a90002dda1 607046b10001dda1
#LMEM 3e0  0x0000000000000000 0000000000000000 0000000000000000 000000003154ca6a
#
#1  parcel_copy_done @ 0x6506
#    Prev_PC  0x6503 -> 0x6506
#
#2  jump_to_parcel_trap @ 0x6507
#    Prev_PC  0x6506 -> 0x6507
#
#3  hw_trap_base @ 0x0000
#    GPR27    0x10b0108167000010 -> 0x10b0108167000072
#    Prev_PC  0x6507 -> 0x0000
#        IR0  0x001a5751 -> 0x00000200
#        IR1  0x00000000 -> 0x00000220
#    LMEM[0x7]  0x007e000000000000 -> 0x007e000020000000
#
#4  process_parcel @ 0x00dc
#    GPR28    0x0000000000000008 -> 0x0000000000000000
#    Prev_PC  0x0000 -> 0x00dc
#
#5  move_to_per_thread_queue @ 0x00de
#ASYNC XTXN REORDER_HASH(PA 0x0000178c)
#    Prev_PC  0x00dc -> 0x00de
#
#6  init_context_registers @ 0x00dd
#    Prev_PC  0x00de -> 0x00dd
#        WP0  0x0000 -> 0x0200
#    LMEM[0x68]  0x000000027798c815 -> 0x000000027798cf09
#    LMEM[0x69]  0x8303e03fe0001000 -> 0x7cb1e03fe0001000
#
#7  init_context_registers_2 @ 0x00df
#    GPR18    0x3fff23fc00000000 -> 0x0000000000000000
#    GPR28    0x0000000000000000 -> 0x0000000000000008
#    Prev_PC  0x00dd -> 0x00df
#        IR0  0x00000200 -> 0x00000000
#
#8  init_context_registers_3 @ 0x00e2
#    Prev_PC  0x00df -> 0x00e2
#        WP2  0x0000 -> 0x0220
#        IR0  0x00000000 -> 0x047f0800
#        IR1  0x00000220 -> 0x000003e0
#
#9  init_context_registers_4 @ 0x00e3
#    GPR18    0x0000000000000000 -> 0x3fff23fc00000000
#    Prev_PC  0x00e2 -> 0x00e3
#
#10  init_context_registers_5 @ 0x00e4
#    Prev_PC  0x00e3 -> 0x00e4
#
#11  init_context_lmem @ 0x00e5
#    Prev_PC  0x00e4 -> 0x00e5
#        IR0  0x047f0800 -> 0x03e0047f
#
#12  init_rw_ext_buf @ 0x00e6
#    Prev_PC  0x00e5 -> 0x00e6
#        WP0  0x0200 -> 0x0180
#
#13  init_rewrite_buffer @ 0x00e7
#    GPR28    0x0000000000000008 -> 0x0000410000000008
#    Prev_PC  0x00e6 -> 0x00e7
#
#14  demux_stream_range @ 0x00e8
#    Prev_PC  0x00e7 -> 0x00e8
#        IR1  0x000003e0 -> 0x00000015
#
#15  handle_special @ 0x00eb
#    GPR00    0xe3ff000000000000 -> 0xe3fc7f0000000000
#    Prev_PC  0x00e8 -> 0x00eb
#
#16  check_rfc2544_lb_stream @ 0x00ed
#    Prev_PC  0x00eb -> 0x00ed
#        IR1  0x00000015 -> 0x00000003
#
#17  load_stream_entry @ 0x00ec
#SYNC XTXN DMEM_RD(VA 0xc020fe -> PA 0xc00020fe)
#    Reply64 is 0xb6018e101a25c000
#    Prev_PC  0x00ed -> 0x00ec
#        XRS  0x323334353637beef -> 0xb6018e101a25c000
#
#18  process_ix_cookie @ 0x00f3
#    GPR00    0xe3fc7f0000000000 -> 0xe3fc7fc000000000
#    GPR13    0x0000000000000000 -> 0x000047f000000000
#    Prev_PC  0x00ec -> 0x00f3
#        IR1  0x00000003 -> 0x00000000
#
#19  process_stream_info @ 0x00f5
#    GPR02    0x1800000000300000 -> 0xb6018e101a25c000
#    Prev_PC  0x00f3 -> 0x00f5
#
#20  process_stream_cnt @ 0x00f6
#ASYNC XTXN COUNTER_INCREMENT(PA 0xc000d12e, 0x00000072)
#    Prev_PC  0x00f5 -> 0x00f6
#
#21  entry_handle_host_or_tunnel @ 0x00f8
#    Prev_PC  0x00f6 -> 0x00f8
#
#22  entry_handle_host_or_tunnel_2 @ 0x0262
#    Prev_PC  0x00f8 -> 0x0262
#
#23  entry_handle_host_or_tunnel_3 @ 0x63cc
#    Prev_PC  0x0262 -> 0x63cc
#
#24  handle_host_layer2 @ 0x63ce
#    Prev_PC  0x63cc -> 0x63ce
#
#25  handle_host_layer2_set_reorder_queue @ 0x63e0
#ASYNC XTXN REORDER_HASH(PA 0x0000178c)
#    GPR12    0x0000000000000000 -> 0x4ff2000000000000
#    Prev_PC  0x63ce -> 0x63e0
#       PCSD  0 -> 1, added 0x0800
#
#26  send_xm_qmove_parcel @ 0x01b8
#    GPR30    0x0000000000000000 -> 0x0000200000000000
#    Prev_PC  0x63e0 -> 0x01b8
#        WP0  0x0180 -> 0x16c0
#        IR1  0x00000000 -> 0x00005000
#
#27  init_qmna_lu @ 0x0296
#    Prev_PC  0x01b8 -> 0x0296
#    LMEM[0x5b]  0x00068030b2000000 -> 0x0000004ff2000000
#
#28  issue_qmna_lu @ 0x0297
#ASYNC XTXN REORDER_SEND(PA 0x800052d8, 0x00000000)
#Packet (h_h 5 @ 0x2d8 h_t 0 @ 0x0):
#    0000004ff2
#        Prev_PC  0x0296 -> 0x0297
#       PCSD  1 -> 0, dropped 0x0800
#
#29  handle_host_layer2_redirect @ 0x63e1
#    Prev_PC  0x0297 -> 0x63e1
#
#30  handle_host_layer2_call_restore_ctx @ 0x63e2
#    Prev_PC  0x63e1 -> 0x63e2
#       PCSD  0 -> 1, added 0x63e3
#
#31  entry_restore_ctx_from_fab_hdr @ 0x0168
#    GPR28    0x0000410000000008 -> 0x0001450000000008
#    Prev_PC  0x63e2 -> 0x0168
#        IR0  0x03e0047f -> 0x00000000
#        IR1  0x00005000 -> 0x80010000
#
#32  restore_ctx_from_fab_hdr_2 @ 0x01cc
#    GPR27    0x10b0108167000072 -> 0x10b0108167000062
#    Prev_PC  0x0168 -> 0x01cc
#        WP3  0x0000 -> 0x02a0
#
#33  restore_ctx_from_fab_hdr_3 @ 0x01cd
#    GPR31    0x0000000000000000 -> 0x8001000000000000
#    Prev_PC  0x01cc -> 0x01cd
#        IR1  0x80010000 -> 0x00008200
#    LMEM[0x3e]  0x2048000000000001 -> 0x8001000000000000
#
#34  restore_ctx_from_fab_hdr_4 @ 0x01ce
#    Prev_PC  0x01cd -> 0x01ce
#    LMEM[0x6]  0x0000000000000000 -> 0x0000820000000000
#
#35  restore_ctx_from_fab_hdr_5 @ 0x01cf
#    GPR28    0x0001450000000008 -> 0x0001450008000008
#    Prev_PC  0x01ce -> 0x01cf
#       PCSD  1 -> 0, dropped 0x63e3
#
#36  handle_host_layer2_2 @ 0x63e3
#    Prev_PC  0x01cf -> 0x63e3
#        WP2  0x0220 -> 0x02a0
#    LMEM[0x3e]  0x8001000000000000 -> 0x7001000000000000
#    LMEM[0x40]  0x00000018000000ff -> 0x0000000000000000
#
#37  handle_host_layer2_3 @ 0x63e5
#    Prev_PC  0x63e3 -> 0x63e5
#    LMEM[0x3e]  0x7001000000000000 -> 0x7009000000000000
#
#38  egress_host_layer2_set_lmp_ctx_bit @ 0x63e7
#    GPR31    0x8001000000000000 -> 0x8009000000000000
#    Prev_PC  0x63e5 -> 0x63e7
#        WP0  0x16c0 -> 0x0260
#
#39  egress_host_layer2 @ 0x63e8
#    GPR14    0x003f020003000000 -> 0x0000820003000000
#    Prev_PC  0x63e7 -> 0x63e8
#        IR0  0x00000000 -> 0x00020003
#
#40  egress_host_layer2_2 @ 0x63e9
#    Prev_PC  0x63e8 -> 0x63e9
#    LMEM[0x48]  0x01a6ef0001a66f00 -> 0x20003f0001a66f00
#
#41  egress_host_layer2_set_ptype_control @ 0x63f4
#    GPR29    0x0000000000000000 -> 0x1980000000000000
#    GPR31    0x8009000000000000 -> 0x1009000000000000
#    Prev_PC  0x63e9 -> 0x63f4
#
#42  egress_host_layer2_set_ptype_control_2 @ 0x63f7
#    GPR29    0x1980000000000000 -> 0x1981800000000000
#    Prev_PC  0x63f4 -> 0x63f7
#    LMEM[0x3e]  0x7009000000000000 -> 0x1009000000000000
#
#43  egress_host_layer2_set_ptype_control_3 @ 0x63f8
#    Prev_PC  0x63f7 -> 0x63f8
#    LMEM[0x40]  0x0000000000000000 -> 0x1981800000000000
#
#44  egress_host_layer2_read_oif @ 0x63f6
#SYNC XTXN NH_Read(VA 0x0b0003 -> PA 0x000b0003)
#    NH is 0x08341b9800010000: CallNH:desc_ptr:0xd06e6, mode=0, count=0x2
#  0x0d06e4  0 : 0xda0004101f800404
#  0x0d06e5  1 : 0x200203e800800000
#
#                              Traps: nexthop trap
#    Prev_PC  0x63f8 -> 0x63f6
#        XRS  0xb6018e101a25c000 -> 0x08341b9800010000
#
#45  entry_call_table_nh @ 0x0030
#    GPR20    0x00708c98004062a7 -> 0x20683731000162a7
#    Prev_PC  0x63f6 -> 0x0030
#        WP0  0x0260 -> 0x1e38
#        IR0  0x00020003 -> 0x004062a7
#        IR1  0x00008200 -> 0x00708c98
#
#46  call_table_launch_nh @ 0x0410
#Cond SYNC XTXN NH_Read(VA 0x0d06e4 -> PA 0x000d06e4)
#    NH is 0xda0004101f800404: IndexNH:key:0x80/0 PROTOCOL, desc_ptr=0x10407e, max=8, nbits=4
#
#                              Traps: nexthop trap
#    Prev_PC  0x0030 -> 0x0410
#        XRS  0x08341b9800010000 -> 0xda0004101f800404
#    LMEM[0x78]  0x00708c980040ffe1 -> 0x00708c98004062a7
#
#47  NO THREAD STATE:  NH Trap pending before and after.
#
#48  entry_set_oif_nh @ 0x0027 (pending hw_trap_base @ 0x0000)
#    GPR11    0xffffff0000000000 -> 0x10407f0000000000
#    Prev_PC  0x003b -> 0x0027
#        WP0  0x1e38 -> 0x1e00
#        XRS  0xda0004101f800404 -> 0xe03ffffc8000ffff
#        IR0  0x004062a7 -> 0x00000008
#        IR1  0x00708c98 -> 0x00003fff
#
#49  set_oif_mtu @ 0x07d3
#    Prev_PC  0x0027 -> 0x07d3
#
#50  trap_nexthop_return_ct @ 0x07d8
#    Prev_PC  0x07d3 -> 0x07d8
#        WP0  0x1e00 -> 0x1e78
#        IR1  0x00003fff -> 0x00000001
#
#51  nh_ret_last @ 0x0419
#Cond SYNC XTXN NH_Read(VA 0x0d06e5 -> PA 0x000d06e5)
#    NH is 0x200203e800800000: UcodeNH: WanOutput Decode: Counter = 0x80fa, proto_cntrs=1
#
#
#                              Traps: nexthop trap
#    Prev_PC  0x07d8 -> 0x0419
#        XRS  0xe03ffffc8000ffff -> 0x200203e800800000
#
#52  entry_ucode_nh @ 0x0024
#    GPR00    0xe3fc7fc000000000 -> 0x200203e800800000
#    GPR20    0x20683731000162a7 -> 0x00708c98004062a7
#    Prev_PC  0x0419 -> 0x0024
#        WP0  0x1e78 -> 0x1e00
#    LMEM[0x6f]  0x0723000000000000 -> 0x00407d0000000000
#
#53  entry_wan_out @ 0x05b0
#    Prev_PC  0x0024 -> 0x05b0
#
#54  wan_out_check_tos_rewrite @ 0x07ef
#    Prev_PC  0x05b0 -> 0x07ef
#
#55  check_tos_rewrite_bridged @ 0x07f7
#    GPR01    0x802081d800000000 -> 0x8000000000000000
#    Prev_PC  0x07ef -> 0x07f7
#       PCSD  0 -> 1, added 0x07fb
#
#56  execute_return @ 0x0095
#    Prev_PC  0x07f7 -> 0x0095
#       PCSD  1 -> 0, dropped 0x07fb
#
#57  wan_out_bridged @ 0x07fb
#    Prev_PC  0x0095 -> 0x07fb
#
#58  init_l2m_reg @ 0x6002
#    GPR01    0x8000000000000000 -> 0xd8bfe00000000000
#    Prev_PC  0x07fb -> 0x6002
#       PCSD  0 -> 1, added 0x6003
#        WP0  0x1e00 -> 0x8480
#        IR0  0x00000008 -> 0x00000010
#
#59  entry_head_tail @ 0x6011
#    GPR05    0x0000000800000000 -> 0x02a0031000000000
#    Prev_PC  0x6002 -> 0x6011
#
#60  head_tail_adj_layer2_ether @ 0x035c
#    Prev_PC  0x6011 -> 0x035c
#       PCSD  1 -> 0, dropped 0x6003
#
#61  init_l2m_select_queue @ 0x6003
#    GPR01    0xd8bfe00000000000 -> 0xd8bfe00010000000
#    Prev_PC  0x035c -> 0x6003
#        WP0  0x8480 -> 0x0f07
#
#62  init_l2m_reg_32lsbits @ 0x6014
#    Prev_PC  0x6003 -> 0x6014
#
#63  encap_done @ 0x601c
#    GPR01    0xd8bfe00010000000 -> 0xd8bfe00010000008
#    Prev_PC  0x6014 -> 0x601c
#
#64  return_from_add_tunnel_hdr @ 0x601f
#    GPR02    0xb6018e101a25c000 -> 0xb6f18e101a25c000
#    GPR03    0x0010e80000000000 -> 0x00f0e80000000000
#    Prev_PC  0x601c -> 0x601f
#
#65  compute_cnt_idx_2 @ 0x6021
#    GPR02    0xb6f18e101a25c000 -> 0xb6018e101a25c000
#    GPR03    0x00f0e80000000000 -> 0x0000e80000000000
#    Prev_PC  0x601f -> 0x6021
#
#66  prep_lifetime @ 0x6022
#    Prev_PC  0x6021 -> 0x6022
#        IR1  0x00000001 -> 0x00000062
#
#67  check_mtu @ 0x6023
#    GPR02    0xb6018e101a25c000 -> 0x00018e101a25c000
#    Prev_PC  0x6022 -> 0x6023
#        IR0  0x00000010 -> 0x00000000
#
#68  write_l2m_info @ 0x602b
#    Prev_PC  0x6023 -> 0x602b
#    LMEM[0x3b]  0xd0bfff4008000000 -> 0xd0bfff4005b1e304
#
#69  l2m_xm_set_parcel_type_unordered @ 0x0397
#    GPR01    0xd8bfe00010000008 -> 0xe8bfe00010000008
#    Prev_PC  0x602b -> 0x0397
#
#70  l2m_set_tail_entry @ 0x0398
#    Prev_PC  0x0397 -> 0x0398
#
#71  keep_tail_entry @ 0x039e
#    GPR01    0xe8bfe00010000008 -> 0xecbfe00010000008
#    Prev_PC  0x0398 -> 0x039e
#        WP0  0x0f07 -> 0x0ef7
#        IR0  0x00000000 -> 0x00000002
#    LMEM[0x3b]  0xd0bfff4005b1e304 -> 0xd0bfff4005b10001
#
#72  write_l2m_stat_info @ 0x03a4
#    Prev_PC  0x039e -> 0x03a4
#        WP0  0x0ef7 -> 0x0ecf
#    LMEM[0x3b]  0xd0bfff4005b10001 -> 0xd0b0000080fa0001
#
#73  skip_accurate_stat @ 0x6030
#    Prev_PC  0x03a4 -> 0x6030
#        IR0  0x00000002 -> 0x00000007
#
#74  write_l2m_header @ 0x6038
#    Prev_PC  0x6030 -> 0x6038
#       PCSD  0 -> 1, added 0x6039
#        WP0  0x0ecf -> 0x0e8f
#        IR0  0x00000007 -> 0x0000000f
#        IR1  0x00000062 -> 0x00000000
#    LMEM[0x3a]  0x2000000100010001 -> 0x20ecbfe000100000
#    LMEM[0x3b]  0xd0b0000080fa0001 -> 0x08b0000080fa0001
#
#75  xm_wait_for_ack @ 0x0275
#    Prev_PC  0x6038 -> 0x0275
#       PCSD  1 -> 0, dropped 0x6039
#
#76  init_xtxn_fields @ 0x6039
#    GPR01    0xecbfe00010000008 -> 0x8c5fe1d100000008
#    Prev_PC  0x0275 -> 0x6039
#        IR1  0x00000000 -> 0x00000016
#
#77  ptp_timestamp_done @ 0x03aa
#    GPR01    0x8c5fe1d100000008 -> 0x8c40f1d100000054
#    Prev_PC  0x6039 -> 0x03aa
#
#78  send_pkt_terminate_if_all_done @ 0x03ae
#    Prev_PC  0x03aa -> 0x03ae
#
#79  send_pkt_terminate_if_all_done_2 @ 0x03bc
#Cond SYNC XTXN REORDER_TERMINATE_SEND(PA 0x8c40f1d1, 0x00000054)
#Packet (h_h 15 @ 0x1d1 h_t 98 @ 0x54):
#    ecbfe00010000008
#    b0000080fa0001
#                  00
#    00bead835580711f
#    8282950800450000
#    54f8dc000040014d
#    b00d0d0d020d0d0d
#    0108002813f41c0a
#    6c5921fd9200018f
#    ab08090a0b0c0d0e
#    0f10111213141516
#    1718191a1b1c1d1e
#    1f20212223242526
#    2728292a2b2c2d2e
#    2f30313233343536
#    37
#    Prev_PC  0x03ae -> 0x03bc

#Above ttrace decoded with http://10.219.49.145/ttrace/index.php
#
#This packet is from the host 
#The packet is destined to WAN out 
#
#
#The packet is forwarded to WAN Q 8 
#
#
# The Outgoing IFL is 131075 
#
#
#==============================================
#             PACKET DUMP     
#==============================================
#Frame 1: 98 bytes on wire (784 bits), 98 bytes captured (784 bits)
#    Encapsulation type: Ethernet (1)
#    Arrival Time: May 16, 2017 10:23:55.000000000 TLT
#    [Time shift for this packet: 0.000000000 seconds]
#    Epoch Time: 1494897835.000000000 seconds
#    [Time delta from previous captured frame: 0.000000000 seconds]
#    [Time delta from previous displayed frame: 0.000000000 seconds]
#    [Time since reference or first frame: 0.000000000 seconds]
#    Frame Number: 1
#    Frame Length: 98 bytes (784 bits)
#    Capture Length: 98 bytes (784 bits)
#    [Frame is marked: False]
#    [Frame is ignored: False]
#    [Protocols in frame: eth:ip:icmp:data]
#Ethernet II, Src: JuniperN_82:82:95 (80:71:1f:82:82:95), Dst: NtiGroup_ad:83:55 (00:00:be:ad:83:55)
#    Destination: NtiGroup_ad:83:55 (00:00:be:ad:83:55)
#        Address: NtiGroup_ad:83:55 (00:00:be:ad:83:55)
#        .... ..0. .... .... .... .... = LG bit: Globally unique address (factory default)
#        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
#    Source: JuniperN_82:82:95 (80:71:1f:82:82:95)
#        Address: JuniperN_82:82:95 (80:71:1f:82:82:95)
#        .... ..0. .... .... .... .... = LG bit: Globally unique address (factory default)
#        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
#    Type: IP (0x0800)
#Internet Protocol Version 4, Src: 13.13.13.2 (13.13.13.2), Dst: 13.13.13.1 (13.13.13.1)
#    Version: 4
#    Header length: 20 bytes
#    Differentiated Services Field: 0x00 (DSCP 0x00: Default; ECN: 0x00: Not-ECT (Not ECN-Capable Transport))
#        0000 00.. = Differentiated Services Codepoint: Default (0x00)
#        .... ..00 = Explicit Congestion Notification: Not-ECT (Not ECN-Capable Transport) (0x00)
#    Total Length: 84
#    Identification: 0xf8dc (63708)
#    Flags: 0x00
#        0... .... = Reserved bit: Not set
#        .0.. .... = Don't fragment: Not set
#        ..0. .... = More fragments: Not set
#    Fragment offset: 0
#    Time to live: 64
#    Protocol: ICMP (1)
#    Header checksum: 0x4db0 [validation disabled]
#        [Good: False]
#        [Bad: False]
#    Source: 13.13.13.2 (13.13.13.2)
#    Destination: 13.13.13.1 (13.13.13.1)
#    [Source GeoIP: Unknown]
#    [Destination GeoIP: Unknown]
#Internet Control Message Protocol
#    Type: 8 (Echo (ping) request)
#    Code: 0
#    Checksum: 0x2813 [correct]
#    Identifier (BE): 62492 (0xf41c)
#    Identifier (LE): 7412 (0x1cf4)
#    Sequence number (BE): 2668 (0x0a6c)
#    Sequence number (LE): 27658 (0x6c0a)
#    Data (56 bytes)
#
#0000  59 21 fd 92 00 01 8f ab 08 09 0a 0b 0c 0d 0e 0f   Y!..............
#0010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f   ................
#0020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f    !"#$%&'()*+,-./
#0030  30 31 32 33 34 35 36 37                           01234567
#        Data: 5921fd9200018fab08090a0b0c0d0e0f1011121314151617...
#        [Length: 56]

#cleanup ttrace stuff 
print "show ttrace" #gives you ttrace captures that are on the box 
print "bringup ttrace x finish   <where x is the ttrace index from above>"
print "bringup ttrace x retire   <where x is the ttrace index from above>"
print "bringup ttrace x delete   <where x is the ttrace index from above>"
print "show ttrace    <verify no ttrace is left on the box after done"


#enable background noise after ttrace is completed
print "Run these after doing ttrace:\n"
print "test jnh %s pfe-liveness start" % (pfe_value)
print "test fabric self_ping enable %s" % (pfe_value)
print "set host_loopback enable-periodic\n\n" 


#Capture matching notes: 

#You can match up to 16 hex nibbles or 8 bytes
#Ethertypes: 0x0800, 0x8100, 0x86dd, 0x8847
#Ethertype plus IPv4: 08004500
#Ethtertype plus 6 bytes of MPLS label: 8847<6 bytes of label>
#Complete Source and destination IPs for IPv4
#Part of either source or destination IP for ipv6
#DMAC or SMAC of Ethernet header
#Specific pattern you can specify in data or ping packet
#Try to Google packet formats and then try to find unique patterns which will give you specific matches

