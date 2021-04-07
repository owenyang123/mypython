#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from isd_tools_dev.modules import nsm as nsm1
from dxd_tools_dev.modules import (jukebox,nsm,hercules)
import re
import pandas as pd
import collections
import re
import subprocess
import argparse
import sys
import re
import os
import yaml
import jinja2
import concurrent.futures
from time import perf_counter
from jinja2 import Template

'''
This script gets list of vc-bar devices in-servce from Jukebox, parses hercules config for 
each device to get P2P ip towards br-agg and loopback and stores them in two separate lists. Loops
over P2P ip list and verfies if the ip is in loopback list
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

def concurr_f(func, xx: list, *args, **kwargs) -> list:
    """This is the concurrency function to use multithreading

    Args:
        func ([type]): Any function to be passed
        xx (list): List of devices

    Returns:
        list: Final list
    """    
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        device_info = {executor.submit(func, x, *args, **kwargs): x for x in xx}
        for future in concurrent.futures.as_completed(device_info):
            _ = device_info[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                pass
    return f_result if f_result else None

def get_hercules_config(device):
    """This function fetches hercules config in set format.

    Args:
        device ([string]): device name, ex: fra50-vc-car-r1
    
    Returns:
        Device config from hercules in set format
    """    
    try:
        raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    raw_config_dict = {}
    raw_config_dict[device] = raw_config
    return raw_config_dict

def get_device_loopback(device):
    """This function gets the device loopback

    Args:
        device ([str]): device name

    Returns:
        loopback_ip (string) : Loopback ip address of the device
        device_info.loopback (list) : List of links the device connects to
    """
    try:
        device_info = jukebox.DeviceOverview(device)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()   
    #get device loopback and device links
    loopback_ip = str(device_info.loopback)
    loopback_dict =  {}
    loopback_dict[device] = loopback_ip
    return loopback_dict

def vc_bar_ip_audit(regions : list):
    vc_bar_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting list of vc-bars , this will take few minutes\n',bcolors.ENDC)
    for region in regions:
        bar_list = jukebox.get_all_devices_in_jukebox_region(region,devicetype='bar',device_states=["in-service"])
        vc_bar_list = vc_bar_list + bar_list

    loopback_list = []
    p2p_list = []
    print(bcolors.OKGREEN,f'[Info] : Getting ips from hercules config to validate\n',bcolors.ENDC)
    loopback_info, raw_config = concurr_f(get_device_loopback, vc_bar_list), concurr_f(get_hercules_config, vc_bar_list)
    for info in loopback_info:
        for device,loopback in info.items():
            loopback_list.append(loopback)
            
    for info in raw_config:
        for k,v in info.items():
            for line in v:
                if re.match("set interfaces .* unit (10|11) family inet address ",line):
                    p2p_list.append(line.split('address')[-1].split('/')[0].strip())

    for ip in p2p_list:
        if ip in loopback_list:
            print(bcolors.FAIL,f'{ip} is duplicate with loopback ip - Please check the ip under NSM',bcolors.ENDC)

    duplicate_ip_list = [ip for ip in p2p_list if p2p_list.count(ip) >=2]
    duplicate_ips = ','.join(duplicate_ip_list)

    if len(duplicate_ip_list) != 0:
        duplicate_ips = ','.join(duplicate_ip_list)
        print(bcolors.FAIL,f'Found following ips re-used on other vc-bars {duplicate_ips}',bcolors.ENDC)

def main():
    start_time = perf_counter()
    regions = ['bom','hkg','icn','kix','nrt','sin','syd','arn','bah','cdg','dub','fra','lhr','mxp','cpt','cmh','iad','sfo','pdx','cmh','yul','gru']
    vc_bar_ip_audit(regions)
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
