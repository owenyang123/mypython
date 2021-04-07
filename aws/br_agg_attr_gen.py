#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

####################################################################################################
#  Summary: Script to generate GB attributes for DX Pre-stage on BR-AGG routers.
#  Description: This script can be used to generate BR-AGG customer-vpc  attributes for DX. The script supports cutsheet in CSV format and can generate attributes for multiple BR-AGGs in a single run. Since the script takes two files as arguments, it will check if the hostnames in the cutsheet match those in BGP attribute file.
#  wiki: https://w.amazon.com/bin/view/EC2/Networking/jasguo/BR_AGG_DX_CONFIG_GEN/ 
#
#  Version: 0.9
#  Author : jasguo@
####################################################################################################

import argparse
import re
import sys
from pathlib import Path
from getpass import getuser

parser = argparse.ArgumentParser(description = "## Generator for DX Pre-stage Config on BR-AGG ##", epilog = 'Guide wiki: https://w.amazon.com/bin/view/EC2/Networking/jasguo/BR_AGG_DX_CONFIG_GEN/')

parser.add_argument("-ints_csv", help = "Path of interface cutsheet in CSV format")
parser.add_argument("-bgp_attr", help = "BGP attribute file path")
parser.add_argument("-ae", nargs = "*", metavar = 'aeN', help = "LAG interface ID", default = [])

args = parser.parse_args()

args.br_dict = {}
args.bgp_dict = {}
args.remdev = []

def peer_ip(ip_str):
    ip_list = ip_str.split(".")
    ip_list[3] = str(int(ip_list[3])+1)
    return ".".join(ip_list)

def mask_removal(ip_str):
    ip_list = ip_str.split('/')
    ip_no_mask = ip_list[0]
    return ip_no_mask

def GB_dir():
    user = getuser()
    GB_path = input('GenevaBuilder Directory(Default: /home/' + user + '/GenevaBuilder/): ')
    if not GB_path:
        GB_path = '/home/' + user + '/GenevaBuilder/'

    GbDir = Path(GB_path)
    if GbDir.is_dir():
        return GB_path
    else:
        raise ValueError("GB directory is invalid.")

def load_GB_attr(GB_path, BR_AGG):
    GB_file = Path(GB_path + "targetspec/border/" + BR_AGG + "/customer-vpc-" + BR_AGG[0:3] + ".attr")

    if GB_file.is_file():
        print ('''
Existing VPC attribute file found in
                {}
Skip the file and print out the output in Shell
'''.format('\x1b[6;30;47m' + BR_AGG + '\x1b[0m'))
        return None
    else:
        VPC_file = open(GB_path + "targetspec/border/" + BR_AGG + "/customer-vpc-" + BR_AGG[0:3] + ".attr", 'a+')
        return VPC_file

def csv_processor(args_in):
    vc_dict = {}
    with open (args_in.ints_csv) as f:
        lines = f.readlines()        
        for line in lines:
            ints_list = line.split(",")
            for i in range(len(ints_list)):
                search_br = re.search(".*-br-agg-.*", ints_list[i])
                if search_br:
                    br_host = search_br.group().rstrip()
                    if br_host in list(args_in.br_dict.keys()):
                        vc_dict = args_in.br_dict[br_host]
                    else:
                        vc_dict = {}
                    if i == 0:
                        if ints_list[2] not in args_in.ae:
                            args_in.ae.append(ints_list[2])
                            ae_id = args_in.ae[-1]
                        search_vc = re.search('.*-vc-.*', ints_list[-3])
                        vc_idx = -3
                        if not search_vc:
                            search_vc = re.search('.*-vc-.*', ints_list[-1])
                            vc_idx = -1
                        vc_host = search_vc.group().rstrip()
                        if vc_host not in args.remdev:
                            args.remdev.append(vc_host)
                        if vc_host in list(vc_dict.keys()):
                            vc_dict[vc_host][0].append(ints_list[vc_idx - 1])
                            vc_dict[vc_host][1].append(ints_list[1])
                        else:
                            vc_dict[vc_host] = [ints_list[vc_idx - 1]],[ints_list[1]], ae_id
                    elif 4 >= len(ints_list) - i >= 1:
                        if ints_list[i - 2] not in args_in.ae:
                            args_in.ae.append(ints_list[i - 2])
                            ae_id = args_in.ae[-1]
                        vc_host = ints_list[0]
                        if vc_host in list(vc_dict.keys()):
                            vc_dict[vc_host][0].append(ints_list[1])
                            vc_dict[vc_host][1].append(ints_list[i - 1])
                        else:
                            vc_dict[vc_host] = [ints_list[1]],[ints_list[i - 1]], ae_id
                    if vc_host not in args.remdev:
                        args.remdev.append(vc_host)
                    args_in.br_dict[br_host] = vc_dict
    args_in.vc_hosts = list(vc_dict.keys())
    args_in.br_hosts = list(args_in.br_dict.keys())
    

def bgp_attributes(args_in):
    vc_hosts = args_in.vc_hosts
    br_hosts = args_in.br_hosts
    with open(args.bgp_attr) as f:
        csc_conf = ['# CSC BGP']
        inet_conf = ['# INET BGP']
        lines = f.readlines()
        for line in lines[1:]:
            bgp_attrs = line.split(',')
            if bgp_attrs[0].rstrip() not in vc_hosts + br_hosts:
                print('''
=======
ERROR:
{} is listed in BGP attribute file, but not found in cutsheet.
=======
'''.format('\x1b[7;33;41m' + bgp_attrs[0].rstrip() + '\x1b[0m'))
                sys.exit(0)
            elif bgp_attrs[1].rstrip() not in vc_hosts + br_hosts:
                print('''
=======
ERROR:
{} is listed in BGP attribute file, but not found in cutsheet.
=======
'''.format('\x1b[7;33;41m' + bgp_attrs[1].rstrip() + '\x1b[0m'))
                sys.exit(0)

            for i in (2,3):
                bgp_attrs[i] = mask_removal(bgp_attrs[i])

            bgp_dict_vc = {}
            if bgp_attrs[0] in vc_hosts:
                if bgp_attrs[1] not in args_in.bgp_dict.keys():
                    bgp_dict_vc[bgp_attrs[0]] = bgp_attrs[2:5]
                    args_in.bgp_dict[bgp_attrs[1]] = bgp_dict_vc
                elif bgp_attrs[0] not in args_in.bgp_dict[bgp_attrs[1]].keys():
                    args_in.bgp_dict[bgp_attrs[1]][bgp_attrs[0]] = bgp_attrs[2:5]
            elif bgp_attrs[1] in vc_hosts:
                if bgp_attrs[0] not in args_in.bgp_dict.keys():
                    bgp_dict_vc[bgp_attrs[1]] = bgp_attrs[2:5]
                    args_in.bgp_dict[bgp_attrs[0]] = bgp_dict_vc
                elif bgp_attrs[1] not in args_in.bgp_dict[bgp_attrs[0]].keys():
                    args_in.bgp_dict[bgp_attrs[0]][bgp_attrs[1]] = bgp_attrs[2:5]

def br_agg_assembler(args_in):
    br_dx_dict = args_in.br_dict
    bgp_attr_dict = args_in.bgp_dict
    GB_Path = args_in.GB_Path

    for br_agg_name in list(br_dx_dict.keys()):
        VPC_File = load_GB_attr(GB_Path, br_agg_name)


        if not VPC_File:
            print ('''
=================
 {}
================='''.format('\x1b[6;30;47m' + br_agg_name + '\x1b[0m'))

        print ('''## VPC defaults
PREFIXLIST DEFAULT 0.0.0.0/0
CUSTOMER VPC VRF AS 7224
''', file = VPC_File)

        for vc_key in list(br_dx_dict[br_agg_name].keys()):

            int_lists = br_dx_dict[br_agg_name][vc_key]
            comm_pre = 'CUSTOMER VPC IFACE ' + int_lists[2]
            print('''# {title}
{common_pre} REMDEVICE "{vc_hostname}"'''.format( title = vc_key, common_pre = comm_pre, vc_hostname = vc_key), file = VPC_File)
            for i in range(len(int_lists[0])):
                print(comm_pre, 'MEMBER {local} REMPORT {remote}'.format(local = int_lists[1][i], remote = int_lists[0][i]), file = VPC_File)
                bgpX = bgp_attr_dict[br_agg_name][vc_key]
            print(comm_pre, 'VLAN 10 IPADDR', bgpX[1].rstrip()+"/31", file = VPC_File)
            print(comm_pre, 'VLAN 11 IPADDR', bgpX[0].rstrip()+"/31 VRF VPC-TRANSPORT", file = VPC_File)

            print('''
# CSC BGP
CUSTOMER VPC VRF NEIGHIP {NEI_IP} LOCALIP {LOCAL_IP} DESC "{vc_host}" DEVNAME {vc_host_upper} SSO {soo_id} AS 4200007224
'''.format(NEI_IP = peer_ip(bgpX[0].rstrip()), LOCAL_IP = bgpX[0].rstrip(), vc_host = vc_key, vc_host_upper = vc_key.upper(), soo_id = bgpX[2].rstrip()), file = VPC_File)

            print('''# INET BGP
CUSTOMER VPC NEIGHIP {NEI_IP} LOCALIP {LOCAL_IP} DESC "{vc_host}"
'''.format(NEI_IP = peer_ip(bgpX[1].rstrip()), LOCAL_IP = bgpX[1].rstrip(), vc_host = vc_key), file = VPC_File)

        if VPC_File:
            VPC_File.close()
    
if __name__ == "__main__":
    try:
        args.GB_Path = GB_dir()
        csv_processor(args)
        bgp_attributes(args)
        br_agg_assembler(args)
    except ValueError as err:
        print (err)
    except:
        print('Script stopped. Please check the cutsheet/attribute file.')

