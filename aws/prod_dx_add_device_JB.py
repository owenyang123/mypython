#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import sys
from dxd_tools_dev.modules import jukebox
import subprocess
from isd_tools_dev.modules import nsm
from dxd_tools_dev.modules import device_regex
from pexpect import pxssh
import getpass
import re
from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.modules import ws_svc_cidr
import ipaddress


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HIGHGREEN = "\033[1;42m"

def get_ws_svc_cidr(ws_svc_cidr, x):
    cidr_ip = ws_svc_cidr + x
    return(str(cidr_ip))

def bfNameXOrdinal(es_svc_hostname, edgOrdinal, increment, ordinal):
    bf_name = es_svc_hostname[:-4] + 'x'
    az, junk = es_svc_hostname.split('-es-svc-')

    sum_increment_ordinal = str(increment + ordinal)
    suffix = '00' + sum_increment_ordinal
    suffix = suffix[-2:]

    bf_num = str(edgOrdinal) + suffix

    bf_name = az + '-es-svc-x' + bf_num

    return bf_name

def info_to_create_bf_device(es_svc_hostname):
    edgOrdinal = int(es_svc_hostname[-3:])

    o1 = 0
    o2 = 0

    if (edgOrdinal % 2 == 0):
        o1 += 8
        o2 -= 8

        edgOrdinal = edgOrdinal - 1

    a = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 1, o1)
    b = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 2, o1)
    c = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 3, o1)
    d = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 4, o1)
    e = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 5, o1)
    f = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 6, o1)
    g = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 7, o1)
    h = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 8, o1)
    i = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 1, o1)
    j = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 2, o1)
    k = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 3, o1)
    l = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 4, o1)
    m = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 5, o1)
    n = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 6, o1)
    o = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 7, o1)
    p = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 8, o1)
    q = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 9, o2)
    r = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 10, o2)
    s = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 11, o2)
    t = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 12, o2)
    u = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 13, o2)
    v = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 14, o2)
    w = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 15, o2)
    x = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 16, o2)
    y = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 9, o2)
    z = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 10, o2)
    aa = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 11, o2)
    bb = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 12, o2)
    cc = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 13, o2)
    dd = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 14, o2)
    ee = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 15, o2)
    ff = bfNameXOrdinal(es_svc_hostname, edgOrdinal, 16, o2)

    return a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x ,y, z, aa, bb, cc, dd, ee, ff

def interface_vegetron(es_svc_hostname):
    ordinal = int(es_svc_hostname[-3:])

    if (ordinal % 2 == 0):
        eth_interface = ['eth6', 'eth8']
    else:
        eth_interface = ['eth2', 'eth4']

    return eth_interface

def interface_skybridge(es_svc_hostname):
    ordinal = int(es_svc_hostname[-3:])

    if (ordinal % 2 == 0):
        eth_interface = ['eth6', 'eth8']
    else:
        eth_interface = ['eth2', 'eth4']

    return eth_interface

def region_group(region):
    if (region == 'arn'):
        edg_group = 'proddx_group_1'
    elif (region == 'bah'):
        edg_group = 'bah_edg_group_1'
    elif (region == 'bjs'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'bom'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'cdg'):
        edg_group = 'proddx_group_1'
    elif (region == 'cmh'):
        edg_group = 'group_1'
    elif (region == 'cpt'):
        edg_group = 'cpt_edg_group_1'
    elif (region == 'dub'):
        edg_group = 'dub_edg_group_1'
    elif (region == 'fra'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'gru'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'hkg'):
        edg_group = 'hkg_edg_group_1'
    elif (region == 'iad'):
        edg_group = 'iad_edg_group_1'
    elif (region == 'icn'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'kix'):
        edg_group = 'ProdDX-group_1'
    elif (region == 'lhr'):
        edg_group = 'group_1'
    elif (region == 'mxp'):
        edg_group = 'mxp_edg_group_1'
    elif (region == 'nrt'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'osu'):
        edg_group = 'Prod-DX'
    elif (region == 'pdt'):
        edg_group = 'Prod-DX on VPN-VPN2 Pool'
    elif (region == 'pdx'):
        edg_group = 'pdx_edg_group_1'
    elif (region == 'sfo'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'sin'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'syd'):
        edg_group = 'Prod-DX on VPC-VPN2 Pool'
    elif (region == 'yul'):
        edg_group = 'yul_group_1'
    elif (region == 'zhy'):
        edg_group = 'ProdDX-group_1'

    return edg_group

# function to add devices to JB
def add_devices_JB(hostname, vendor, device_model, serial_number, ipv4_numr, ipv6_numr, region, ws_svc_prefix, rack_type, rack_type_string):
    print(bcolors.HEADER, "adding device to JB...", bcolors.ENDC)

    edg_group = region_group(region)

    # create connection
    device_new = jukebox.create_coral_device(
        hostname, vendor, device_model, serial_number, ipv4_numr, ipv6_numr, region, edg_group, rack_type_string)

    es_svc_hostname = hostname.replace("vc-edg", "es-svc")
    ws_svc_hostname = hostname.replace("vc-edg", "ws-svc")

    ws_svc_cidr_info = ws_svc_prefix + "/31"
    print(bcolors.HEADER, "adding link CIDR for ws-svc in JB", bcolors.ENDC)
    print(ws_svc_prefix)
    print(bcolors.HEADER, "adding link CIDR for es-svc in JB", bcolors.ENDC)

    # link cidr for JB
    link_cidr_list = jukebox.cidr_info(hostname, es_svc_hostname, "10.0.0.2/31", "", "ec2", link_cidr_list=[])
    link_cidr_list = jukebox.cidr_info(hostname, ws_svc_hostname, ws_svc_cidr_info, "", "prod", link_cidr_list)

    if (rack_type == 1):
        # cabling list for JB
        print(" adding voltron15 cabling into JB...")
        cabling_list = jukebox.device_cabling("xe-0/0/16:0", hostname, ws_svc_hostname, "xe-0/0/32", cabling_list=[])
        cabling_list = jukebox.device_cabling("xe-0/0/16:1", hostname, ws_svc_hostname, "xe-0/0/33", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/16:2", hostname, ws_svc_hostname, "xe-0/0/34", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/16:3", hostname, ws_svc_hostname, "xe-0/0/35", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:0", hostname, ws_svc_hostname, "xe-0/0/36", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:1", hostname, ws_svc_hostname, "xe-0/0/37", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:2", hostname, ws_svc_hostname, "xe-0/0/38", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:3", hostname, ws_svc_hostname, "xe-0/0/39", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/18:0", hostname, ws_svc_hostname, "xe-0/0/40", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/18:1", hostname, ws_svc_hostname, "xe-0/0/41", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/18:2", hostname, ws_svc_hostname, "xe-0/0/42", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/18:3", hostname, ws_svc_hostname, "xe-0/0/43", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:0", hostname, ws_svc_hostname, "xe-0/0/44", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:1", hostname, ws_svc_hostname, "xe-0/0/45", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:2", hostname, ws_svc_hostname, "xe-0/0/46", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:3", hostname, ws_svc_hostname, "xe-0/0/47", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/20:0", hostname, ws_svc_hostname, "xe-0/0/48:0", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/20:1", hostname, ws_svc_hostname, "xe-0/0/48:1", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/20:2", hostname, ws_svc_hostname, "xe-0/0/48:2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/20:3", hostname, ws_svc_hostname, "xe-0/0/48:3", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/21:0", hostname, ws_svc_hostname, "xe-0/0/49:0", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/21:1", hostname, ws_svc_hostname, "xe-0/0/49:1", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/21:2", hostname, ws_svc_hostname, "xe-0/0/49:2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/21:3", hostname, ws_svc_hostname, "xe-0/0/49:3", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/22:0", hostname, ws_svc_hostname, "xe-0/0/50:0", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/22:1", hostname, ws_svc_hostname, "xe-0/0/50:1", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/22:2", hostname, ws_svc_hostname, "xe-0/0/50:2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/22:3", hostname, ws_svc_hostname, "xe-0/0/50:3", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/23:0", hostname, ws_svc_hostname, "xe-0/0/51:0", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/23:1", hostname, ws_svc_hostname, "xe-0/0/51:1", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/23:2", hostname, ws_svc_hostname, "xe-0/0/51:2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/23:3", hostname, ws_svc_hostname, "xe-0/0/51:3", cabling_list)

        bf_hostname = info_to_create_bf_device(es_svc_hostname)

        cabling_list = jukebox.device_cabling("xe-0/0/4:0", hostname, bf_hostname[0], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/4:1", hostname, bf_hostname[1], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/4:2", hostname, bf_hostname[2], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/4:3", hostname, bf_hostname[3], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/5:0", hostname, bf_hostname[4], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/5:1", hostname, bf_hostname[5], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/5:2", hostname, bf_hostname[6], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/5:3", hostname, bf_hostname[7], "eth2", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/6:0", hostname, bf_hostname[8], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/6:1", hostname, bf_hostname[9], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/6:2", hostname, bf_hostname[10], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/6:3", hostname, bf_hostname[11], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/7:0", hostname, bf_hostname[12], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/7:1", hostname, bf_hostname[13], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/7:2", hostname, bf_hostname[14], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/7:3", hostname, bf_hostname[15], "eth4", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/8:0", hostname, bf_hostname[16], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/8:1", hostname, bf_hostname[17], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/8:2", hostname, bf_hostname[18], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/8:3", hostname, bf_hostname[19], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:0", hostname, bf_hostname[20], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:1", hostname, bf_hostname[21], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:2", hostname, bf_hostname[22], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:3", hostname, bf_hostname[23], "eth6", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/10:0", hostname, bf_hostname[24], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/10:1", hostname, bf_hostname[25], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/10:2", hostname, bf_hostname[26], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/10:3", hostname, bf_hostname[27], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:0", hostname, bf_hostname[28], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:1", hostname, bf_hostname[29], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:2", hostname, bf_hostname[30], "eth8", cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:3", hostname, bf_hostname[31], "eth8", cabling_list)

        jukebox.add_new_device_to_jb(device_new, cabling_list, link_cidr_list, site)
        ddb.add_device_to_dx_region_table(region, hostname)

    elif (rack_type == 2):
        bf_hostname = es_svc_hostname.replace("r", "x")

        # cabling list for vegetron
        print(" adding vegetron cabling into JB...")
        cabling_list = jukebox.device_cabling("et-0/0/0", hostname, ws_svc_hostname, "et-0/0/1", cabling_list=[])
        cabling_list = jukebox.device_cabling("et-0/0/16", hostname, ws_svc_hostname, "et-0/0/17", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/24", hostname, ws_svc_hostname, "et-0/0/25", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/8", hostname, ws_svc_hostname, "et-0/0/9", cabling_list)

        eth_interface = interface_vegetron(es_svc_hostname)

        cabling_list = jukebox.device_cabling("xe-0/0/1:0", hostname, bf_hostname + '01', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/1:1", hostname, bf_hostname + '01', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/1:2", hostname, bf_hostname + '02', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/1:3", hostname, bf_hostname + '02', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:0", hostname, bf_hostname + '03', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:1", hostname, bf_hostname + '03', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:2", hostname, bf_hostname + '04', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:3", hostname, bf_hostname + '04', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:0", hostname, bf_hostname + '05', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:1", hostname, bf_hostname + '05', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:2", hostname, bf_hostname + '06', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:3", hostname, bf_hostname + '06', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:0", hostname, bf_hostname + '07', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:1", hostname, bf_hostname + '07', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:2", hostname, bf_hostname + '08', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:3", hostname, bf_hostname + '08', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:0", hostname, bf_hostname + '09', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:1", hostname, bf_hostname + '09', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:2", hostname, bf_hostname + '10', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:3", hostname, bf_hostname + '10', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:0", hostname, bf_hostname + '11', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:1", hostname, bf_hostname + '11', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:2", hostname, bf_hostname + '12', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:3", hostname, bf_hostname + '12', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:0", hostname, bf_hostname + '13', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:1", hostname, bf_hostname + '13', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:2", hostname, bf_hostname + '14', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:3", hostname, bf_hostname + '14', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:0", hostname, bf_hostname + '15', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:1", hostname, bf_hostname + '15', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:2", hostname, bf_hostname + '16', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:3", hostname, bf_hostname + '16', eth_interface[1], cabling_list)

        jukebox.add_new_device_to_jb(device_new, cabling_list, link_cidr_list, site)
        ddb.add_device_to_dx_region_table(region, hostname)


    elif (rack_type == 3):
        bf_hostname = es_svc_hostname.replace("r", "x")

        # cabling list for skybridge_l
        print(" adding skybridge_l cabling into JB...")
        cabling_list = jukebox.device_cabling("et-0/0/0", hostname, ws_svc_hostname, "et-0/0/1", cabling_list=[])
        cabling_list = jukebox.device_cabling("et-0/0/2", hostname, ws_svc_hostname, "et-0/0/3", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/4", hostname, ws_svc_hostname, "et-0/0/5", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/8", hostname, ws_svc_hostname, "et-0/0/9", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/10", hostname, ws_svc_hostname, "et-0/0/11", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/12", hostname, ws_svc_hostname, "et-0/0/13", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/14", hostname, ws_svc_hostname, "et-0/0/15", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/16", hostname, ws_svc_hostname, "et-0/0/17", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/18", hostname, ws_svc_hostname, "et-0/0/19", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/20", hostname, ws_svc_hostname, "et-0/0/21", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/24", hostname, ws_svc_hostname, "et-0/0/25", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/26", hostname, ws_svc_hostname, "et-0/0/27", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/28", hostname, ws_svc_hostname, "et-0/0/29", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/30", hostname, ws_svc_hostname, "et-0/0/31", cabling_list)

        eth_interface = interface_skybridge(es_svc_hostname)

        cabling_list = jukebox.device_cabling("xe-0/0/1:0", hostname, bf_hostname + '01', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/1:1", hostname, bf_hostname + '01', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/1:2", hostname, bf_hostname + '02', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/1:3", hostname, bf_hostname + '02', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:0", hostname, bf_hostname + '03', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:1", hostname, bf_hostname + '03', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:2", hostname, bf_hostname + '04', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/3:3", hostname, bf_hostname + '04', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:0", hostname, bf_hostname + '05', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:1", hostname, bf_hostname + '05', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:2", hostname, bf_hostname + '06', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/9:3", hostname, bf_hostname + '06', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:0", hostname, bf_hostname + '07', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:1", hostname, bf_hostname + '07', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:2", hostname, bf_hostname + '08', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/11:3", hostname, bf_hostname + '08', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:0", hostname, bf_hostname + '09', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:1", hostname, bf_hostname + '09', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:2", hostname, bf_hostname + '10', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/17:3", hostname, bf_hostname + '10', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:0", hostname, bf_hostname + '11', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:1", hostname, bf_hostname + '11', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:2", hostname, bf_hostname + '12', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/19:3", hostname, bf_hostname + '12', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:0", hostname, bf_hostname + '13', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:1", hostname, bf_hostname + '13', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:2", hostname, bf_hostname + '14', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/25:3", hostname, bf_hostname + '14', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:0", hostname, bf_hostname + '15', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:1", hostname, bf_hostname + '15', eth_interface[1], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:2", hostname, bf_hostname + '16', eth_interface[0], cabling_list)
        cabling_list = jukebox.device_cabling("xe-0/0/27:3", hostname, bf_hostname + '16', eth_interface[1], cabling_list)

        jukebox.add_new_device_to_jb(device_new, cabling_list, link_cidr_list, site)
        ddb.add_device_to_dx_region_table(region, hostname)

    elif (rack_type == 4):
        bf_hostname = es_svc_hostname.replace("r", "x")

        # cabling list for skybridge
        print(" adding skybridge cabling into JB...")
        cabling_list = jukebox.device_cabling("et-0/0/0", hostname, ws_svc_hostname, "et-0/0/1", cabling_list=[])
        cabling_list = jukebox.device_cabling("et-0/0/2", hostname, ws_svc_hostname, "et-0/0/3", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/8", hostname, ws_svc_hostname, "et-0/0/9", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/14", hostname, ws_svc_hostname, "et-0/0/15", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/18", hostname, ws_svc_hostname, "et-0/0/19", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/20", hostname, ws_svc_hostname, "et-0/0/21", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/24", hostname, ws_svc_hostname, "et-0/0/25", cabling_list)
        cabling_list = jukebox.device_cabling("et-0/0/26", hostname, ws_svc_hostname, "et-0/0/27", cabling_list)

        eth_interface = interface_skybridge(es_svc_hostname)

        if (int(bf_hostname[-3:]) % 2 != 0):
            cabling_list = jukebox.device_cabling("et-0/0/1", hostname, bf_hostname + '01', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/3", hostname, bf_hostname + '02', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/9", hostname, bf_hostname + '03', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/15", hostname, bf_hostname + '04', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/19", hostname, bf_hostname + '05', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/21", hostname, bf_hostname + '06', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/25", hostname, bf_hostname + '07', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/27", hostname, bf_hostname + '08', 'eth2', cabling_list)
        elif (int(bf_hostname[-3:]) % 2 == 0):
            cabling_list = jukebox.device_cabling("et-0/0/1", hostname, bf_hostname + '09', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/3", hostname, bf_hostname + '10', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/9", hostname, bf_hostname + '11', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/15", hostname, bf_hostname + '12', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/19", hostname, bf_hostname + '13', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/21", hostname, bf_hostname + '14', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/25", hostname, bf_hostname + '15', 'eth2', cabling_list)
            cabling_list = jukebox.device_cabling("et-0/0/27", hostname, bf_hostname + '16', 'eth2', cabling_list)

        jukebox.add_new_device_to_jb(device_new, cabling_list, link_cidr_list, site)



## MAIN ##
x = 0 # needed for cidr iteration


vendor = "Juniper"
ipv6_numr = ''
username = "root"

devices = input("input the list of devices (ex. gru4-4-vc-edg-r[202-205]):")
rack_type_string = input("rack type(voltron15 or vegetron or skybridge_l or skybridge):")

if rack_type_string == "voltron15":
    rack_type = 1
elif rack_type_string == "vegetron":
    rack_type = 2
elif rack_type_string == "skybridge_l":
    rack_type = 3
elif rack_type_string =="skybridge":
    rack_type = 4

if not (rack_type==1 or rack_type==2 or rack_type==3 or rack_type==4):
    print("1=voltron15 | 2=vegetron | 3=skybridge_l | 4=skybridge")
    print('exiting...')
    sys.exit()


device_list = device_regex.get_device_list_from_regex(devices)

print(device_list)

###### new code for skybridge stuff #####
first_device = device_list[0]
last_device = device_list[-1]
ws_svc_cidr = input("ws-svc link cidr:")
ws_svc_cidr = ipaddress.ip_address(ws_svc_cidr)
######

if (device_list == False):
    sys.exit()

site = re.search(r'([a-z][a-z][a-z].+?)-', devices).group(1)
password = getpass.getpass(prompt="Please Enter Root Password:")
region = devices[:3]

for hostname in device_list:
    try:
        s = pxssh.pxssh()
        print(bcolors.HEADER, "connecting to Device {}".format(
            hostname), bcolors.ENDC)
        s.login(hostname, username, password, original_prompt=r"[%>#$]", login_timeout=25)
        s.prompt(timeout=6)
        print(bcolors.HEADER, "please be patient...", bcolors.ENDC)

        # vme address and gw address
        s.sendline('cli')  # run a command
        s.prompt(timeout=6)
        s.sendline('show interface terse vme')
        s.prompt(timeout=5)  # match the prompt
        cli = str(s.before)
        print(bcolors.HEADER, "Getting the vme and GW IPs", bcolors.ENDC)
        vme_ip = re.search(
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}', cli).group()
        ipv4_numr, junk = vme_ip.split("/")

        # get the serial number and model number
        s.sendline('show chassis hardware | match Chassis')
        s.prompt(timeout=5)  # match the prompt
        cli2 = str(s.before)
        print(bcolors.HEADER, "Getting the SN and device model", bcolors.ENDC)
        serial_number = re.search(
            r'Chassis\s+(\w+)\s+(\w+-\w+-\w+)', cli2).group(1)
        device_model = re.search(
            r'Chassis\s+(\w+)\s+(\w+-\w+-\w+)', cli2).group(2)

        # get the os version
        s.sendline('show version | match Junos')
        s.prompt(timeout=5)  # match the prompt
        cli3 = str(s.before)
        print(bcolors.HEADER, "Getting the os version", bcolors.ENDC)
        os_version = re.search(r'Junos:\s(\w+\.\w+\-\w+\.\w+)', cli3).group(1)

        ws_svc_prefix = get_ws_svc_cidr(ws_svc_cidr, x)

        add_devices_JB(hostname, vendor, device_model, serial_number,
                       ipv4_numr, ipv6_numr, region, ws_svc_prefix, rack_type, rack_type_string)

        x = x + 4

        # exit the program
        s.sendline("exit")
        print(bcolors.HEADER, "exiting..", bcolors.ENDC)
        s.prompt(timeout=5)
        s.sendline ( "logout" )
        print(bcolors.OKGREEN, "device have been added to JB", bcolors.ENDC)
    except pxssh.ExceptionPxssh as e:
        print(bcolors.FAIL, "SSH failed on login.", bcolors.ENDC)
        print(bcolors.WARNING,"Can you SSH to the device using username:root and password:Juniper123?", bcolors.ENDC)
        print(bcolors.WARNING,"Is your .ssh file up to date?", bcolors.ENDC)
        print(bcolors.FAIL, "is VME interface up/up?", bcolors.ENDC)
        print(e)