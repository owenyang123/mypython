#!/bin/python

from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell
import argparse
import time
import os
import warnings
import threading
from lxml import etree
from xml.dom.minidom import parse, parseString
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import re
import json


parser = argparse.ArgumentParser(description = '''
        PFE/CLI output for interface in MPC9E
        '''
        )
parser.add_argument('IP', help = 'ip address of router')
parser.add_argument('INTERFACE', help = 'interface name, e.g: xe-1/0/0')
parser.add_argument('USER', help = 'username' )
parser.add_argument('PASSWORD', help = 'password' )
parser.add_argument('--version', '-v' , action = 'version', version = '%(prog)s 0.1')
args = parser.parse_args()
# Print provided arguments
print("IP address: {}, INTERFACE name: {}, USER name: {}, PASSWORD: {} ".format(args.IP, args.INTERFACE, args.USER, args.PASSWORD))


def xml_pprint(element):
    s = ET.tostring(element)
    print(minidom.parseString(s).toprettyxml())

def xml_pprint_text(element):
    t = ET.tostring(element)
    print(t)
####################################


def get_interface_speed(ifname, dev):
    interface_lxml_element = dev.rpc.get_interface_information(interface_name=ifname)
    parse_string = minidom.parseString(ET.tostring(interface_lxml_element))
    speed = str(parse_string.getElementsByTagName("speed")[0].firstChild.data).strip()
    return speed

def get_fpc_pic_port(ifname):
    split_ifname_full = ifname.split("-")[1]
    split_ifname = split_ifname_full.split(":")[0]
    split_ifname_no_slash = split_ifname.split("/")
    fpc_slot = split_ifname_no_slash[0]
    pic_slot = split_ifname_no_slash[1]
    port = split_ifname_no_slash[2]
    return fpc_slot, pic_slot, port

def get_fpc_pic_type(fpc_slot, pic_slot, dev):
    fpc_slot = "FPC " + fpc_slot
    mic_slot = "MIC " + pic_slot
    fpc_lxml_element = dev.rpc.get_chassis_inventory()
    parse_string = minidom.parseString(ET.tostring(fpc_lxml_element))
    chassis_modules = parse_string.getElementsByTagName("chassis-module")
    for chassis_module in chassis_modules:
        chassis_module_name = str(chassis_module.getElementsByTagName("name")[0].firstChild.data)
        fpc = re.match(".*FPC ", chassis_module_name)
        if fpc:
            if ( chassis_module_name == fpc_slot):
                fpc_type = chassis_module.getElementsByTagName("description")[0].firstChild.data
                chassis_sub_modules = chassis_module.getElementsByTagName("chassis-sub-module")
                for chassis_sub_module in chassis_sub_modules:
                    chassis_sub_module_name = str(chassis_sub_module.getElementsByTagName("name")[0].firstChild.data)
                    mic = re.match("(.*MIC.)", chassis_sub_module_name)
                    if mic:
                        if (chassis_sub_module_name == mic_slot):
                            mic_type = str(chassis_sub_module.getElementsByTagName("description")[0].firstChild.data)
    return fpc_type, mic_type


def get_pfe_number(fpc_slot, pic_slot, dev, ifname):
    show_interface = "show interfaces " + ifname
    pfe_interface_command = dev.rpc.request_pfe_execute(target = 'fpc' + fpc_slot, command = show_interface)
    pfe_interface_command_string = ET.tostring(pfe_interface_command)
    pfe_interface_command_string_interation = iter(pfe_interface_command_string)
    for line in pfe_interface_command_string.splitlines():
        #print(line)
        line_split = line.split(",")
        for op_line in line_split:
            if "Global PFE" in op_line:
                global_pfe = op_line.split(":")[1]
                local_pfe = int(global_pfe) % 4
    return global_pfe, local_pfe

def get_mqss_data(fpc_slot, pfe_num_local, ifname, dev, filename):
    file = open('/home/tkazmierczak/python/logs/' + filename, 'a')
    show_mqss = 'show mqss %s ifd %s' %(str(pfe_num_local), ifname)
    pfe_command = dev.rpc.request_pfe_execute(target = 'fpc' + fpc_slot, command = show_mqss)
    pfe_command_string = ET.tostring(pfe_command)
    # print(pfe_command_string)
    file.write("--------------> MQSS <--------------\n")
    file.write(pfe_command_string)
    for line in pfe_command_string.splitlines():
        if "IFD index" in line:
            ifd_index = line.split(":")[1]
        elif "Ingress PHY streams" in line:
            ingress_phy_streams = line.split(":")[1]
        elif "Egress PHY streams" in line:
            egress_phy_streams = line.split(":")[1]
        elif "MAC type" in line:
            mac_type = line.split(":")[1]
    file.close()
    return ifd_index, ingress_phy_streams, egress_phy_streams, mac_type

def  get_mac_state(dev, ifname, fpc_type, speed, filename, fpc_slot):
    file = open('/home/tkazmierczak/python/logs/' + filename, 'a')
    if "10Gbps" in speed:
        mtype = "chmac"
        pcstype = "chpcs"
    if "100Gbps" in speed:
        mtype = "cmac"
        pcstype = "cpcs"
    if "40Gbps" in speed:
        mtype = "cmac"
        pcstype = "cpcs"

    mtip_id = "NONE"
    pcs_id = "NONE"
    pattern_mtype = "{mtip_type}"
    pattern_mtipid = "{mtip_id}"
    pattern_mtpcs = "{mtip_pcs}"
    pattern_pcs = "{pcs_id}"
    block_string = "MAC"
    commands = []
    fpc_type = fpc_type.split(" ")[0]

    with open('chipset.json') as json_data:
        data = json.load(json_data)
        for record in data["Category"]:
            if fpc_type in record["chipset"]:
                for block in record["blocks"]:
                    for value in block:
                        if block_string in value:
                            for command in block[value]:
                                commands.append(command)
    #print(commands)
    if commands:
        file.write("--------------> MAC <--------------\n")
        for comm in commands:
            if "show mtip" in comm:
                if pattern_mtype in comm:
                    comm = re.sub(pattern_mtype, mtype, comm)
                if pattern_mtipid in comm:
                    comm = re.sub(pattern_mtipid, mtip_id, comm)
                if pattern_mtpcs in comm:
                    comm = re.sub(pattern_mtpcs, pcstype, comm)
                if pattern_pcs in comm:
                    comm = re.sub(pattern_pcs, pcs_id, comm)
                pfe_command = dev.rpc.request_pfe_execute(target = 'fpc' + fpc_slot, command = comm)
                pfe_command_string = ET.tostring(pfe_command)
                file.write(pfe_command_string)
                if mtype + " summary" in comm:
                    for line in pfe_command_string.splitlines():
                        if ifname in line:
                            mtip_id = line.lstrip(" ").split(" ")[0]
                if pcstype + " summary" in comm:
                    for line in pfe_command_string.splitlines():
                        if ifname in line:
                            pcs_id = line.lstrip(" ").split(" ")[0]
    file.close()
    return mtype, mtip_id, pcstype, pcs_id

def get_wi_precl_stats(fpc_type, fpc_slot, pic_slot, dev, filename):
    file = open('/home/tkazmierczak/python/logs/' + filename, 'a')
    commands = []
    fpc_type = fpc_type.split(" ")[0]
    precl_id = "NONE"
    precl_id_list = []
    pattern_preclid = "{precl_id}"
    block_string = "PREC"
    with open('chipset.json') as json_data:
        data = json.load(json_data)
        for record in data["Category"]:
            if fpc_type in record["chipset"]:
                for block in record["blocks"]:
                    for value in block:
                        if block_string in value:
                            for command in block[value]:
                                commands.append(command)
    if commands:
        file.write("--------------> PRECL <--------------\n")
        for comm in commands:
            if "show precl" in comm:
                if pattern_preclid in comm:
                    for precl_id in precl_id_list:
                        #print(precl_id_list)
                        comm_modify = re.sub(pattern_preclid, precl_id, comm)
                        #print(comm_modify)
                        pfe_command = dev.rpc.request_pfe_execute(target = 'fpc' + fpc_slot, command = comm_modify)
                        pfe_command_string = ET.tostring(pfe_command)
                        file.write(pfe_command_string)
                pfe_command = dev.rpc.request_pfe_execute(target = 'fpc' + fpc_slot, command = comm)
                pfe_command_string = ET.tostring(pfe_command)
                file.write(pfe_command_string)
                if "precl-eng summary" in comm:
                    for line in pfe_command_string.splitlines():
                        if "MQSS_engine" + "." + fpc_slot + "." + pic_slot in line:
                            precl_id_temp = line.lstrip(" ").split(" ")[0]
                            precl_id_list.append(precl_id_temp)
    file.close()

def get_wi_stats(fpc_type, fpc_slot, pfe_number_local, dev, filename, ingress_phy_streams):
    file = open('/home/tkazmierczak/python/logs/' + filename, 'a')
    commands = []
    fpc_type = fpc_type.split(" ")[0]
    pfe_num = str(pfe_number_local)
    stream_rt = str(int(ingress_phy_streams.split(",")[0]) - 1024)
    stream_ctlr = str(int(ingress_phy_streams.split(",")[1]) - 1024)
    stream_be = str(int(ingress_phy_streams.split(",")[2]) - 1024)
    stream_drop = str(int(ingress_phy_streams.split(",")[3]) - 1024)


    pattern_pfe_num = "{pfe_num}"
    pattern_stream_rt = "{stream_rt}"
    pattern_stream_ctlr = "{stream_ctlr}"
    pattern_stream_be = "{stream_be}"
    pattern_stream_drop = "{stream_drop}"
    block_string = "WIN"

    with open('chipset.json') as json_data:
        data = json.load(json_data)
        for record in data["Category"]:
            if fpc_type in record["chipset"]:
                for record in record["blocks"]:
                    for value in record:
                        if block_string in value:
                            for comm in record[value]:
                                commands.append(comm)
    if commands:
        file.write("--------------> WIN <--------------\n")
        for comm in commands:
            if "show" in comm or "test" in comm:
                if pattern_pfe_num in comm:
                    comm = re.sub(pattern_pfe_num, pfe_num, comm)
                if pattern_stream_rt in comm:
                    comm = re.sub(pattern_stream_rt, stream_rt, comm)
                if pattern_stream_ctlr in comm:
                    comm = re.sub(pattern_stream_ctlr, stream_ctlr, comm)
                if pattern_stream_be in comm:
                    comm = re.sub(pattern_stream_be, stream_be, comm)
                if pattern_stream_drop in comm:
                    comm = re.sub(pattern_stream_drop, stream_drop, comm)
            pfe_command = dev.rpc.request_pfe_execute(target = 'fpc' + fpc_slot, command = comm)
            pfe_command_string = ET.tostring(pfe_command)
            file.write(pfe_command_string)
    file.close()


if __name__ == '__main__':
    dev = Device(host = args.IP, user = args.USER, passwd = args.PASSWORD)
    dev.open()
    ifname = args.INTERFACE
    current_time = time.strftime("%c")
    current = []
    current = current_time.split(" ")
    filename = current[1] + current[3] + "_" + current[4] + ".txt"
    filename = filename.replace(":","_")
    speed = get_interface_speed(ifname, dev)
    fpc_slot, pic_slot, port = get_fpc_pic_port(ifname)
    fpc_type, mic_type = get_fpc_pic_type(fpc_slot, pic_slot, dev)
    pfe_number_global, pfe_number_local = get_pfe_number(fpc_slot, pic_slot, dev, ifname)
    ifd_index, ingress_phy_streams, egress_phy_streams, mac_type = get_mqss_data(fpc_slot, pfe_number_local, ifname, dev, filename)
    mtip_type, mtip_id, pcs_type, pcs_id = get_mac_state(dev, ifname, fpc_type, speed, filename, fpc_slot)
    get_wi_precl_stats(fpc_type, fpc_slot, pic_slot, dev, filename)
    get_wi_stats(fpc_type, fpc_slot, pfe_number_local, dev, filename, ingress_phy_streams)
    print("==============================================================================================")
    print("Interface: {}".format(ifname))
    print("FPC_slot: {}".format(fpc_slot))
    print("PIC_slot: {}".format(pic_slot))
    print("Port_number: {}".format(port))
    print("FPC type: {}".format(fpc_type))
    print("MIC type: {}".format(mic_type))
    print("Global PFE: {}".format(pfe_number_global))
    print("Local PFE: {}".format(pfe_number_local))
    print("IFD index: {}".format(ifd_index))
    print("Ingress PHY Streams: {}".format(ingress_phy_streams))
    print("Egress PHY Streams: {}".format(egress_phy_streams))
    print("MAC type: {}".format(mac_type))
    print("Interface speed: {}".format(speed))
    dev.close()



'''
#MPC9E PFE outputs example:
=============================

SMPC0(mx2020-GNF1-re1 vty)# show jspec client

 ID       Name
  1       MPCS[0]
  2       XR2CHIP[0]
  3       XR2CHIP[2]
  4       XR2CHIP[4]
  5       XR2CHIP[6]
  6       XR2CHIP[1]
  7       XR2CHIP[3]
  8       XR2CHIP[5]
  9       XR2CHIP[7]
 10       EACHIP[0]
 11       EACHIP[1]
 12       EACHIP[2]
 13       EACHIP[3]
 14       MPCS[1]
 15       MPCS[2]

SMPC0(mx2020-GNF1-re1 vty)# show version
Juniper Embedded Microkernel Version 17.4X48-D11.1
<..>
SMPC platform (1750Mhz Intel(R) Atom(TM) CPU processor, 3136MB memory, 8192KB flash)
Current time   : May 26 16:33:29.42409
Elapsed time   :      1+15:20:08


SMPC0(mx2020-GNF1-re1 vty)# show mqss 0 ifd xe-0/0/0:0

IFD information
---------------

IFD name                 : xe-0/0/0:0
IFD index                : 252
Ingress PHY streams      : 1165, 1166, 1167, 1277
Egress PHY streams       : 1092
MAC type                 : CHMAC
MAC set                  : 0
MAC port number          : 0
Avago SERDES numbers     : 2

SMPC0(mx2020-GNF1-re1 vty)#

SMPC0(mx2020-GNF1-re1 vty)# show mtip-chmac summary
 ID mtip_chmac name        FPC PIC Port Chan ASIC inst link ifd            (ptr)
--- ---------------------- --- --- ---- ---- ---- ---- ---- -------------- --------
  1 mtip_chmac.0.0.56:0     0   0   56    0    0    0   0                  e36cf630
  2 mtip_chmac.0.0.57:0     0   0   57    0    0    0   0                  e36cf4b0
  3 mtip_chmac.0.0.0:0      0   0    0    0    0    0   0   xe-0/0/0:0     e36cea30
  4 mtip_chmac.0.0.0:1      0   0    0    1    0    0   1   xe-0/0/0:1     e36ce970
  5 mtip_chmac.0.0.0:2      0   0    0    2    0    0   2   xe-0/0/0:2     e36ce8b0
  6 mtip_chmac.0.0.0:3      0   0    0    3    0    0   3   xe-0/0/0:3     e36ce7f0
  7 mtip_chmac.0.0.1:0      0   0    1    0    0    0   4   xe-0/0/1:0     39800678
  8 mtip_chmac.0.0.1:1      0   0    1    1    0    0   5   xe-0/0/1:1     398005b8
  9 mtip_chmac.0.1.58:0     0   1   58    0    0    0   0                  398004f8
<..>

SMPC0(mx2020-GNF1-re1 vty)# show mtip-chpcs summary
 ID mtip_chpcs name        FPC PIC Port Chan ifd                  (ptr)
--- ---------------------- --- --- ---- ---- ------------------ --------
  1 mtip_chpcs.0.0.0:0      0   0    0   0  xe-0/0/0:0           394c2038
  2 mtip_chpcs.0.0.0:1      0   0    0   1  xe-0/0/0:1           39591290
  3 mtip_chpcs.0.0.0:2      0   0    0   2  xe-0/0/0:2           39662500
  4 mtip_chpcs.0.0.0:3      0   0    0   3  xe-0/0/0:3           39731758
  5 mtip_chpcs.0.0.1:0      0   0    1   0  xe-0/0/1:0           398009b0
  6 mtip_chpcs.0.0.1:1      0   0    1   1  xe-0/0/1:1           398cfc08
  7 mtip_chpcs.0.0.1:2      0   0    1   2  xe-0/0/1:2           39a48028
  8 mtip_chpcs.0.0.1:3      0   0    1   3  xe-0/0/1:3           39b1d2c8
  9 mtip_chpcs.0.0.2:0      0   0    2   0  xe-0/0/2:0           39bea508
<..>

SMPC0(mx2020-GNF1-re1 vty)# show precl-eng summary
 ID  precl_eng name       FPC PIC   (ptr)
--- -------------------- ---- ---  --------
  1 MQSS_engine.0.0.56     0   0  39361b40
  2 MQSS_engine.0.0.57     0   0  3937e870
  3 MQSS_engine.0.1.58     0   1  3993cf60
  4 MQSS_engine.0.1.59     0   1  3995a2a8

SMPC0(mx2020-GNF1-re1 vty)# show precl-eng 0 statistics

SMPC0(mx2020-GNF1-re1 vty)# [May 26 23:57:58.561 LOG: Err] precl_eng: not a valid index 0
[May 26 23:57:58.561 LOG: Err] engine 0 unavailable.

SMPC0(mx2020-GNF1-re1 vty)# show precl-eng 1 statistics
         stream    Traffic
 port      ID       Class             TX pkts               RX pkts          Dropped pkts
------  -------  ----------          ---------             ---------        --------------
  00      1165        RT          0000000000000000      0000000000000000    0000000000000000
  00      1166        CTRL        0000000000000000      0000000000000000    0000000000000000
  00      1167        BE          0000000000000000      0000000000000000    0000000000000000

  01      1169        RT          0000000000000000      0000000000000000    0000000000000000
  01      1170        CTRL        0000000000000000      0000000000000000    0000000000000000
  01      1171        BE          0000000000000000      0000000000000000    0000000000000000
<..>

SMPC0(mx2020-GNF1-re1 vty)# show precl-eng 1 configured-my-macs
Configured Global My-Mac Addresses
---------------------
Configured Global My-Mac Addresses
Port 00: Hardware My-Mac :   00:90:69:22:1a:00  &  ff:ff:ff:ff:ff:ff
Port 01: Hardware My-Mac :   00:90:69:22:1a:01  &  ff:ff:ff:ff:ff:ff
Port 02: Hardware My-Mac :   00:90:69:22:1a:02  &  ff:ff:ff:ff:ff:ff
Port 03: Hardware My-Mac :   00:90:69:22:1a:03  &  ff:ff:ff:ff:ff:ff
Port 04: Hardware My-Mac :   00:90:69:22:1a:04  &  ff:ff:ff:ff:ff:ff
Port 05: Hardware My-Mac :   00:90:69:22:1a:05  &  ff:ff:ff:ff:ff:ff
Port 06: Hardware My-Mac :   00:90:69:22:1a:06  &  ff:ff:ff:ff:ff:ff
Port 07: Hardware My-Mac :   00:90:69:22:1a:07  &  ff:ff:ff:ff:ff:ff
Port 08: Hardware My-Mac :   00:90:69:22:1a:08  &  ff:ff:ff:ff:ff:ff
Port 09: Hardware My-Mac :   00:90:69:22:1a:09  &  ff:ff:ff:ff:ff:ff
Port 10: Hardware My-Mac :   00:90:69:22:1a:0a  &  ff:ff:ff:ff:ff:ff
Port 11: Hardware My-Mac :   00:90:69:22:1a:0b  &  ff:ff:ff:ff:ff:ff
Port 12: Hardware My-Mac :   00:90:69:22:1a:0c  &  ff:ff:ff:ff:ff:ff
Port 13: Hardware My-Mac :   00:90:69:22:1a:0d  &  ff:ff:ff:ff:ff:ff
Port 14: Hardware My-Mac :   00:90:69:22:1a:0e  &  ff:ff:ff:ff:ff:ff
Port 15: Hardware My-Mac :   00:90:69:22:1a:0f  &  ff:ff:ff:ff:ff:ff
Port 16: Hardware My-Mac :   00:90:69:22:1a:10  &  ff:ff:ff:ff:ff:ff
Port 17: Hardware My-Mac :   00:90:69:22:1a:11  &  ff:ff:ff:ff:ff:ff
Port 18: Hardware My-Mac :   00:90:69:22:1a:12  &  ff:ff:ff:ff:ff:ff
Port 19: Hardware My-Mac :   00:90:69:22:1a:13  &  ff:ff:ff:ff:ff:ff
Port 20: Hardware My-Mac :   00:90:69:22:1a:14  &  ff:ff:ff:ff:ff:ff
Port 21: Hardware My-Mac :   00:90:69:22:1a:15  &  ff:ff:ff:ff:ff:ff
Port 22: Hardware My-Mac :   00:90:69:22:1a:16  &  ff:ff:ff:ff:ff:ff
Port 23: Hardware My-Mac :   00:90:69:22:1a:17  &  ff:ff:ff:ff:ff:ff

SMPC0(mx2020-GNF1-re1 vty)#

SMPC0(mx2020-GNF1-re1 vty)# show mqss 0 wi stats

WI statistics
-------------

WI debug statistics
-------------------

sbucket_fc[0]       : 0x00000000_00000000_00000000_00000000
sbucket_fc[1]       : 0x00000000_00000000_00000000_00000000
pbucket_fc          : 0x0
wsch_stall_hi       : 0
wsch_stall_lo       : 0
malloc_usemeter     : 0
bcmw_usemeter       : 0

Total incoming statistics
-------------------------

----------------------------------------------------------------
Counter Name      Total                 Rate
----------------------------------------------------------------
Received Packets  5391272               23 pps
Received Bytes    743667279             14000 bps
Flushed Packets   0                     0 pps
----------------------------------------------------------------

Oversubscription drop statistics
--------------------------------

------------------------------------------------------------------------------------------
MAC  Total Dropped Packets Dropped Packets      Total Dropped Bytes  Dropped Bytes Rate
Port                       Rate (pps)                                (bps)
------------------------------------------------------------------------------------------
0    0                     0                    0                    0
1    0                     0                    0                    0
2    0                     0                    0                    0
3    0                     0                    0                    0
4    0                     0                    0                    0
5    0                     0                    0                    0
6    0                     0                    0                    0
7    0                     0                    0                    0
8    0                     0                    0                    0
9    0                     0                    0                    0
10   0                     0                    0                    0
11   0                     0                    0                    0
12   0                     0                    0                    0
13   0                     0                    0                    0
14   0                     0                    0                    0
15   0                     0                    0                    0
16   0                     0                    0                    0
17   0                     0                    0                    0
18   0                     0                    0                    0
19   0                     0                    0                    0
20   0                     0                    0                    0
21   0                     0                    0                    0
22   0                     0                    0                    0
23   0                     0                    0                    0
24   0                     0                    0                    0
25   0                     0                    0                    0
26   0                     0                    0                    0
27   0                     0                    0                    0
28   0                     0                    0                    0
29   0                     0                    0                    0
30   0                     0                    0                    0
31   0                     0                    0                    0
32   0                     0                    0                    0
33   0                     0                    0                    0
34   0                     0                    0                    0
35   0                     0                    0                    0
36   0                     0                    0                    0
37   0                     0                    0                    0
38   0                     0                    0                    0
39   0                     0                    0                    0
40   0                     0                    0                    0
41   0                     0                    0                    0
42   0                     0                    0                    0
43   0                     0                    0                    0
44   0                     0                    0                    0
45   0                     0                    0                    0
46   0                     0                    0                    0
47   0                     0                    0                    0
------------------------------------------------------------------------------------------

Tracked stream statistics
-------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------
Track Stream Stream Total Packets        Packets Rate         Total Bytes          Bytes Rate           Total EOPE           EOPE Rate
      Mask   Match                       (pps)                                     (bps)                                     (pps)
-------------------------------------------------------------------------------------------------------------------------------------------------
0     0xff   0x8d   0                    0                    0                    0                    0                    0
1     0x0    0x0    5391272              23                   743667279            14000                0                    0
2     0x0    0x0    5391272              23                   743667279            14000                0                    0
3     0x0    0x0    5391272              23                   743667279            14000                0                    0
4     0x0    0x0    5391272              23                   743667279            14000                0                    0
5     0x0    0x0    5391272              23                   743667279            14000                0                    0
6     0x0    0x0    5391272              23                   743667279            14000                0                    0
7     0x0    0x0    5391272              23                   743667279            14000                0                    0
8     0x0    0x0    5391272              23                   743667279            14000                0                    0
9     0x0    0x0    5391272              23                   743667279            14000                0                    0
10    0x0    0x0    5391272              23                   743667279            14000                0                    0
11    0x0    0x0    5391272              23                   743667279            14000                0                    0
12    0x0    0x0    5391272              23                   743667279            14000                0                    0
13    0x0    0x0    5391272              23                   743667279            14000                0                    0
14    0x0    0x0    5391272              23                   743667279            14000                0                    0
15    0x0    0x0    5391272              23                   743667279            14000                0                    0
16    0x0    0x0    5391272              23                   743667279            14000                0                    0
17    0x0    0x0    5391272              23                   743667279            14000                0                    0
18    0x0    0x0    5391272              23                   743667279            14000                0                    0
19    0x0    0x0    5391272              23                   743667279            14000                0                    0
20    0x0    0x0    5391272              23                   743667279            14000                0                    0
21    0x0    0x0    5391272              23                   743667279            14000                0                    0
22    0x0    0x0    5391272              23                   743667279            14000                0                    0
23    0x0    0x0    5391272              23                   743667279            14000                0                    0
24    0x0    0x0    5391272              23                   743667279            14000                0                    0
25    0x0    0x0    5391272              23                   743667279            14000                0                    0
26    0x0    0x0    5391272              23                   743667279            14000                0                    0
27    0x0    0x0    5391272              23                   743667279            14000                0                    0
28    0x0    0x0    5391272              23                   743667279            14000                0                    0
29    0x0    0x0    5391272              23                   743667279            14000                0                    0
30    0x0    0x0    5391272              23                   743667279            14000                0                    0
31    0x0    0x0    5391272              23                   743667279            14000                0                    0
32    0x0    0x0    5391272              23                   743667279            14000                0                    0
33    0x0    0x0    5391272              23                   743667279            14000                0                    0
34    0x0    0x0    5391272              23                   743667279            14000                0                    0
35    0x0    0x0    5391272              23                   743667279            14000                0                    0
36    0x0    0x0    5391272              23                   743667279            14000                0                    0
37    0x0    0x0    5391272              23                   743667279            14000                0                    0
38    0x0    0x0    5391272              23                   743667279            14000                0                    0
39    0x0    0x0    5391272              23                   743667279            14000                0                    0
40    0x0    0x0    5391272              23                   743667279            14000                0                    0
41    0x0    0x0    5391272              23                   743667279            14000                0                    0
42    0x0    0x0    5391272              23                   743667279            14000                0                    0
43    0x0    0x0    5391272              23                   743667279            14000                0                    0
44    0x0    0x0    5391272              23                   743667279            14000                0                    0
45    0x0    0x0    5391272              23                   743667279            14000                0                    0
46    0x0    0x0    5391272              23                   743667279            14000                0                    0
47    0x0    0x0    5391272              23                   743667279            14000                0                    0
-------------------------------------------------------------------------------------------------------------------------------------------------

SMPC0(mx2020-GNF1-re1 vty)#

'''

