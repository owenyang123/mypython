#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from isd_tools_dev.modules import (nsm,ddb)
from dxd_tools_dev.modules import (jukebox,hercules)
from dxd_tools_dev.datastore import ddb as ddb_dxd
import re
import sys
import argparse
import os
import logging
import time
import re
from time import perf_counter
from multiprocessing import Pool

'''
This script will give the requirements for MPLSoUDP for pop/az

Author: anudeept@
Version: 1.1

usage: mplsudp_prereq.py [-h] [-a] [-vc]

Script for scaling on vc devices towards border

optional arguments:
  -h, --help       show this help message and exit
  -a , --az        AZ, EXAMPLE : iad12
  -vc , --vc_car   VC CAR, EXAMPLE : iad66-vc-car-r1
'''

class bcolors:
	CLEARBLUE = '\033[96m'
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	WARNING = '\033[93m'
	OKGREEN = '\033[92m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Script for scaling on vc devices towards border")
    parser.add_argument("-a","--az",type=str, metavar = '', required = False, help = 'AZ, EXAMPLE : iad12')
    parser.add_argument("-vc","--vc_car",type=str, metavar = '', required = False, help = 'VC CAR, EXAMPLE : iad66-vc-car-r1') 
    return parser.parse_args()

def az_prereq(az):
    """This function returns MPLSoUDP MTU requirement for vc-bars and br-aggs in an AZ
    Function gives the list of vc-bars/br-aggs and the interfaces that does not meet MTU requirements

    Args:
        az ([string]): AZ where vc-bars and br-aggs are located ex: 'iad12'
    """
    region = az[0:3]
    vc_bar_list = jukebox.get_all_devices_in_jukebox_region(region,devicetype='bar',device_states=["in-service","configured"])
    vc_bar_az_list = []
    br_agg_list = []
    
    for vc_bar in vc_bar_list:
        if f'{az}-' in vc_bar:
            vc_bar_az_list.append(vc_bar)

    if vc_bar_az_list == []:
        print(bcolors.FAIL,f'[Info] : {az} does not have any vc-bars')

    device_pattern = ".*(br-agg).*"
    
    vc_bars_in_az = ','.join(vc_bar_az_list)
    print(bcolors.OKGREEN,f'[Info] : List of vc-bars in {az} : {vc_bars_in_az}\n')

    upstream_dict = {}
    for device in vc_bar_az_list:
        upstream_dict[device] = {}
        device_info = nsm.get_raw_device_with_interfaces(device)
        for info in device_info['interfaces']:
            if re.match('ae.*..10',info['name']):
                upstream_dict[device][info['name']] = info['mtu']

    #list of br-agg's that vc-bar's connect to
    print(bcolors.OKGREEN,f'[Info] : Getting list of br-aggs that vc-bars in {az} connect to, this will take few minutes\n',bcolors.ENDC)
    for device in vc_bar_az_list:
        device_info = jukebox.get_device_link(device)
        for info in device_info:
            if re.match(device_pattern, info[0]):
                br_agg_list.append(info[0])

    br_agg_list = list(set(br_agg_list))
    
    br_aggs = ','.join(br_agg_list)
    print(bcolors.OKGREEN,f'[Info] : vc-bars in {az} connnect to {br_aggs}\n',bcolors.ENDC)

    vc_bar_dict = {}
    br_agg_dict = {}
    for device in vc_bar_az_list:
        vc_bar_dict[device] = {}
        device_info = nsm.get_raw_device_with_interfaces(device)
        if device_info['state']['lifecycle_status'] != 'PROVISIONED':
            for info in device_info['interfaces']:
                if re.match('ae.*..10',info['name']):
                    vc_bar_dict[device][info['name']] = info['mtu']
    for device in br_agg_list:
        br_agg_dict[device] = {}
        device_info = nsm.get_raw_device_with_interfaces(device)
        if device_info['state']['lifecycle_status'] != 'PROVISIONED':
            for info in device_info['interfaces']:
                if re.match('ae.*..10',info['name']):
                    br_agg_dict[device][info['name']] = info['mtu']

    bar_1500_dict = {}
    bar_non_mtu_1500_dict = {}
    bar_missing_info_list = []
    for device,info in vc_bar_dict.items():
        if info != {}:
            for lag,mtu in info.items():
                if mtu == '1500':
                    bar_1500_dict[device] = {}
                elif mtu != '1500':
                    bar_non_mtu_1500_dict[device] = {}
        else:
            bar_missing_info_list.append(device)

    br_1500_dict = {}
    br_non_mtu_1500_dict = {}
    br_missing_info_list = []
    for device,info in br_agg_dict.items():
        if info != {}:
            for lag,mtu in info.items():
                if mtu == '1500':
                    br_1500_dict[device] = {}
                elif mtu != '1500':
                    br_non_mtu_1500_dict[device] = {}
        else:
            bar_missing_info_list.append(device)

    for device,info in vc_bar_dict.items():
        if info != {}:
            for lag,mtu in info.items():
                if mtu == '1500':
                    bar_1500_dict[device][lag] = mtu
                elif mtu != '1500':
                    bar_non_mtu_1500_dict[device][lag] = mtu

    for device,info in br_agg_dict.items():
        if info != {}:
            for lag,mtu in info.items():
                if mtu == '1500':
                    br_1500_dict[device][lag] = mtu
                elif mtu != '1500':
                    br_non_mtu_1500_dict[device][lag] = mtu

    for device,lag in bar_1500_dict.items():
        print(bcolors.FAIL,f'{device} does not meet MTU pre-req',bcolors.ENDC)
        for lag_num,mtu in lag.items():
            print(bcolors.FAIL,f'{lag_num} : {mtu}',bcolors.ENDC)

    for device,lag in bar_non_mtu_1500_dict.items():
        print(bcolors.OKGREEN,f'{device} meets MTU pre-req',bcolors.ENDC)

    for device,lag in br_1500_dict.items():
        print(bcolors.FAIL,f'{device} does not meet MTU pre-req',bcolors.ENDC)
        for lag_num,mtu in lag.items():
            print(bcolors.FAIL,f'{lag_num} : {mtu}',bcolors.ENDC)

    for device,lag in br_non_mtu_1500_dict.items():
        print(bcolors.OKGREEN,f'{device} meets MTU pre-req',bcolors.ENDC)
    
    missing_dict = {}
    if len(bar_missing_info_list) != 0:
        for device in bar_missing_info_list:
            mtu_list = []
            missing_dict[device] = {}
            print(bcolors.FAIL,f'Could not get {device} vlan 10 MTU from NSM, parising hercules config',bcolors.ENDC)
            raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
            for line in raw_config:
                if re.match(f"set interfaces ae.* description .*-(br-agg)-",line):
                    if "unit" not in line:
                        ae_num = line.split('description')[0].split('interfaces')[1].strip()
                        for line in raw_config:
                            if re.match(f"set interfaces {ae_num} unit 10 family inet mtu 1500",line):
                                mtu = line.split('mtu')[-1].strip()
                                mtu_list.append(mtu)
            if '1500' in mtu_list:
                print(f'{device} does not meet MTU pre-req')
            else:
                print(f'{device} meets MTU pre-req')

def pop_prereq(vc_car):
    """This function returns MPLSoUDP MTU requirement for VC-CAR
    Function gives the list of br-tra/vc-cor/vc-dar and the interfaces that does not meet MTU requirements

    Args:
        vc_car ([string]): vc-car name ex: 'iad66-vc-car-r1'
    """
    upstream_list = []
    vc_dar_list = []
    device_info = jukebox.get_device_link(vc_car)
    device_pattern = ".*(br-tra|vc-cor|vc-dar).*"
    device_pattern_dar = ".*(br-tra|vc-cor).*"
    
    print(bcolors.OKBLUE,f'[Info] : Getting list of devices that {vc_car} connects to',bcolors.ENDC)
 
    for info in device_info:
        if re.match(device_pattern, info[0]):
            upstream_list.append(info[0])

    for device in upstream_list:
        if 'dar' in device:
            vc_dar_list.append(device)

    if len(vc_dar_list)!= 0:
        for vc_dar in vc_dar_list:
            device_info = jukebox.get_device_link(vc_dar)
            for vc_dar_info in device_info:
                if re.match(device_pattern_dar, vc_dar_info[0]):
                    upstream_list.append(vc_dar_info[0])
    
    upstream_list = list(set(upstream_list))
    upstream_devices = ','.join(upstream_list)
    print(bcolors.OKGREEN,f'[Info] : {vc_car} connects to {upstream_devices}\n',bcolors.ENDC)

    if len(vc_dar_list)!=0:
        vc_dar_devices = ','.join(vc_dar_list)

    print(bcolors.OKBLUE,f'[Info] : Validating interfaces on upstream routerts for MTU towards VC-CARs',bcolors.ENDC)
    upstream_dict = {}
    for device in upstream_list:
        upstream_dict[device] = {}
        device_info = nsm.get_raw_device_with_interfaces(device)
        if device_info['state']['lifecycle_status'] != 'PROVISIONED':
            for info in device_info['interfaces']:
                if re.match('ae.*..10',info['name']):
                    upstream_dict[device][info['name']] = info['mtu']

    mtu_1500_dict = {}
    non_mtu_1500_dict = {}
    for device,info in upstream_dict.items():
        for lag,mtu in info.items():
            if mtu == '1500' and info != {}:
                mtu_1500_dict[device] = {}
            elif mtu != '1500' and info != {}:
                non_mtu_1500_dict[device] = {}

    for device,info in upstream_dict.items():
        for lag,mtu in info.items():
            if mtu == '1500':
                mtu_1500_dict[device][lag] = mtu
            else:
                non_mtu_1500_dict[device][lag] = mtu

    for device,lag in mtu_1500_dict.items():
        print(bcolors.FAIL,f'{device} does not meet MTU pre-req',bcolors.ENDC)
        for lag_num,mtu in lag.items():
            print(bcolors.FAIL,f'{lag_num} : MTU configured {mtu}',bcolors.ENDC)

    non_mtu_list = [device for device in mtu_1500_dict]
    for device in upstream_list:
        if device not in non_mtu_list:
            print(bcolors.OKGREEN,f'{device} meets MTU pre-req',bcolors.ENDC)
            for device_name,lag in non_mtu_1500_dict.items():
                if device == device_name:
                    for lag_num,mtu in lag.items():
                        print(bcolors.OKGREEN,f'{lag_num} : MTU configured {mtu}',bcolors.ENDC)
def main():
    start_time = perf_counter()
    args = parse_args()
    #Validating user arguments
    if args.vc_car:
        pop_prereq(args.vc_car)
    elif args.az:
        az_prereq(args.az)
    else:
        print(bcolors.FAIL,f'[Error] : User did not specify the right argument run --help - Exiting',bcolors.ENDC)
        sys.exit()
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
