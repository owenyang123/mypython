#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from isd_tools_dev.modules import (nsm,ddb)
from dxd_tools_dev.modules import (jukebox,hercules)
from dxd_tools_dev.datastore import ddb as ddb_dxd
import pandas as pd
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
Script to audit devices globally for MPLSoUDP

Author: anudeept@
Version: 1.0

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
    parser = argparse.ArgumentParser(description="SCRIPT FOR GLOBAL AUDIT OF VC DEVICES FOR MPLSOUDP")
    parser.add_argument("-r","--region",type=str, metavar = '', required = True, help = 'SUPPORTED REGIONS: apac,china,emea,itar,nasa')
    parser.add_argument("-d","--device_type",type=str, metavar = '', required = True, help = 'SUPPORTED TYPES: bar,car,cir,edg') 
    return parser.parse_args()


def get_region(region_name : str):
    
    if region_name == 'apac':
        regions = ['bom', 'hkg', 'icn', 'kix','nrt','sin','syd' ]
    elif region_name == 'china':
        regions = ['zhy', 'bjs']
    elif region_name == 'emea':
        regions = ['arn', 'bah', 'cdg', 'dub', 'fra', 'lhr', 'mxp', 'cpt']
    elif region_name == 'nasa':
        regions = ['cmh', 'iad', 'sfo', 'pdx', 'cmh', 'yul', 'gru']
    elif region_name == 'itar':
        regions = ['pdt', 'osu']
    return regions

def vc_bar_audit(region_name : str):
    """Function gets list of vc-bars/br-aggs in region and checks MTU reqiurement and saves to an 
    excel sheet

    Args:
        region_name (str): region, ex: apac,emea,itar,nasa,china
    """
    username = os.getlogin()
    regions = get_region(region_name)
    vc_bar_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting list of vc-bars in region, this will take few minutes\n',bcolors.ENDC)
    for region in regions:
        bar_list = jukebox.get_all_devices_in_jukebox_region(region,devicetype='bar',device_states=["in-service"])
        vc_bar_list = vc_bar_list + bar_list

    vc_bar_dict= {}
    for device in vc_bar_list:
        mtu_list = []
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
            vc_bar_dict[device] = 'Red'
        else:
            vc_bar_dict[device] = 'Green'
    
    df_vc_bar = pd.DataFrame(list(vc_bar_dict.items()),columns = ['device','mtu_status'])
    vc_bar_sheet_name = 'vc_bar_audit_'+region_name+'.xlsx'
    df_vc_bar.to_excel(vc_bar_sheet_name, engine='xlsxwriter',index=None)
    print(bcolors.OKGREEN,f'[Info] :Audit report saved to {username}/{vc_bar_sheet_name}',bcolors.ENDC)

    #Get br-agg info
    device_pattern = ".*(br-agg).*"
    br_agg_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting list of br-aggs that vc-bars in region connect to, this will take few minutes\n',bcolors.ENDC)
    for device in vc_bar_list:
        device_info = jukebox.get_device_link(device)
        for info in device_info:
            if re.match(device_pattern, info[0]):
                br_agg_list.append(info[0])

    br_agg_list = list(set(br_agg_list))
    
    br_aggs = ','.join(br_agg_list)

    br_agg_dict = {}
    for device in br_agg_list:
        mtu_list = []
        raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
        for line in raw_config:
            if re.match(f"set interfaces ae.* description .*-(br-agg)-",line):
                if "unit" not in line and 'tazzy' not in line and 'vc-agg' not in line:
                    ae_num = line.split('description')[0].split('interfaces')[1].strip()
                    for line in raw_config:
                        if re.match(f"set interfaces {ae_num} unit 10 family inet mtu 1500",line):
                            mtu = line.split('mtu')[-1].strip()
                            mtu_list.append(mtu)
        if '1500' in mtu_list:
            br_agg_dict[device] = 'Red'
        else:
            br_agg_dict[device] = 'Green'

    df_br_agg = pd.DataFrame(list(br_agg_dict.items()),columns = ['device','mtu_status'])
    br_agg_sheet_name = 'br_agg_audit_'+region_name+'.xlsx'
    df_br_agg.to_excel(br_agg_sheet_name, engine='xlsxwriter',index=None)
    print(bcolors.OKGREEN,f'[Info] :Audit report saved to {username}/{br_agg_sheet_name}\n',bcolors.ENDC)


def vc_edg_audit(region_name: str):
    """Function gets list of vc-edg in region and saves it to an excel sheet

    Args:
        region_name (str): region, ex: apac,emea,itar,nasa,china
    """
    username = os.getlogin()
    regions = get_region(region_name)

    vc_edg_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting list of vc-edgs in region, this will take few minutes\n',bcolors.ENDC)
 
    for region in regions:
        edg_list = jukebox.get_all_devices_in_jukebox_region(region,devicetype='edg',device_states=["in-service"])
        vc_edg_list = vc_edg_list + edg_list

    mplsudp_vc_edg_list = []
    for device in vc_edg_list:
        device_info = jukebox.get_device_detail(device)
        if 'MX' in device_info.data.device.model or 'mx' in device_info.data.device.model or 'JNP' in device_info.data.device.model:
            mplsudp_vc_edg_list.append(device)
    
    vc_edg_df = pd.DataFrame(mplsudp_vc_edg_list,columns=['device'])
    vc_edg_sheet_name = 'vc_edg_audit_'+region_name+'.xlsx'
    vc_edg_df.to_excel(vc_edg_sheet_name, engine='xlsxwriter',index=None)
    print(bcolors.OKGREEN,f'[Info] :Audit report saved to {username}/{vc_edg_sheet_name}',bcolors.ENDC)

def vc_cir_audit(region_name: str):
    """Function gets list of vc-cirs in region and saves it to an excel sheet

    Args:
        region_name (str): region, ex: apac,emea,itar,nasa,china
    """
    username = os.getlogin()
    regions = get_region(region_name)
    vc_cir_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting list of vc-cirs in region, this will take few minutes\n',bcolors.ENDC)
 
    for region in regions:
        cir_list = jukebox.get_all_devices_in_jukebox_region(region,devicetype='cir',device_states=["in-service"])
        vc_cir_list = vc_cir_list + cir_list

    vc_cir_df = pd.DataFrame(vc_cir_list,columns=['device'])
    vc_cir_sheet_name = 'vc_cir_audit_'+region_name+'.xlsx'
    vc_cir_df.to_excel(vc_cir_sheet_name, engine='xlsxwriter',index=None)
    print(bcolors.OKGREEN,f'[Info] :Audit report saved to {username}/{vc_cir_sheet_name}',bcolors.ENDC)


def vc_car_audit(region_name: str):
    """Function gets list of vc-cars in region and saves it to an excel sheet

    Args:
        region_name (str): region, ex: apac,emea,itar,nasa,china
    """    
    
    username = os.getlogin()
    regions = get_region(region_name)
    vc_car_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting list of vc-cars in region, this will take few minutes\n',bcolors.ENDC)
 
    for region in regions:
        car_list = jukebox.get_all_devices_in_jukebox_region(region,devicetype='car',device_states=["in-service"])
        vc_car_list = vc_car_list + car_list
    vc_car_df = pd.DataFrame(vc_car_list,columns=['device'])
    vc_car_sheet_name = 'vc_car_audit_'+region_name+'.xlsx'
    vc_car_df.to_excel(vc_car_sheet_name, engine='xlsxwriter',index=None)
    print(bcolors.OKGREEN,f'[Info] :Audit report saved to {username}/{vc_car_sheet_name}',bcolors.ENDC)

def main():
    start_time = perf_counter()
    args = parse_args()
    regions = ['china','emea','nasa','itar','apac']
    if args.region in regions:
        print(bcolors.OKGREEN,"User argument for region type is valid",bcolors.ENDC)
    else:
        print(bcolors.FAIL,"User argument for region is not valid, exiting - run help",bcolors.ENDC)
        sys.exit()
    #Validating user arguments
    if args.device_type == 'car':
        vc_car_audit(args.region)
    elif args.device_type == 'bar':
        vc_bar_audit(args.region)
    elif args.device_type == 'edg':
        vc_edg_audit(args.region)
    elif args.device_type == 'cir':
        vc_cir_audit(args.region) 
    else:
        print(bcolors.FAIL,f'[Error] : User did not specify the right argument run --help - Exiting',bcolors.ENDC)
        sys.exit()
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
