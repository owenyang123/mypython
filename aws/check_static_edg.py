#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import jukebox
from dxd_tools_dev.datastore import ddb
from isd_tools_dev.modules import hercules
import sys
import logging
import argparse
import re
import os
import subprocess
import getpass
import time
import json
from dxd_tools_dev.modules import nsm
import concurrent.futures
from os.path import expanduser
import json




def check_hercules(filtered_list):
    print("\n=========Getting Devices Config Please wait========\n")
    result = {}
    for device in filtered_list:
        result[str(device)] = ["1","1"]
        try:
            config = os.popen('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file set-config --uncensored'.format(device)).read().splitlines()
        except:
            log_error = "Could not get config info from Hercules of  {}".format(device)
            logging.error(log_error)
            sys.exit()

        for config_line in config:
            if re.search("set routing-instances MA-PP.*route-dist.*", config_line):
                example = re.search("set routing-instances MA-PP.*route-dist.*", config_line)[0]
                result[device][1] = example 
                result[device][0] = "Found"

                break
            else:
                result[device][1] = "None" 
                result[device][0] = "Not Found"
    return result



def print_result(result):
    print("{:<50} {:<50} {:<50}".format('Device','Static_route','Example'))
    for device in result.keys():
        print("{:<50} {:<50} {:<50}".format(device,result[device][0], result[device][1]))






def get_edges(region):
    print("\n=========Getting All Edges Please wait========\n")
    devices_list = jukebox.get_devices_in_jukebox_region(region)
    edge_list = []
    for device in devices_list:
        if "vc-edg" in device: 
            edge_list.append(device)
    return edge_list





def check_edges(edge_list):
    print("\n===============Finding the Commercial Edges Please wait====================\n") 
    commercial_edg_groups_list = list()
    remove_from_list = list()
    region_edg_list = list()
    filtered_edge_list = list()
    edge_devices_dict = {}
    for edge_device in edge_list:
        region_edg_list.append(edge_device.split('-')[0])
    region_edg_list = list(set(region_edg_list))
    for region_edg in region_edg_list:
        for group in jukebox.get_site_region_details(region_edg).region.edg_groups:
            if 'ExternalCustomer' == group.edg_group_type:
                commercial_edg_groups_list.append(group.name)
        edge_devices_dict[region_edg] = list(set(commercial_edg_groups_list))    
    for edge_device in edge_list:
        try:
            edge_device_group_name = jukebox.get_device_detail(edge_device).data.device.edg_group
            if edge_device_group_name in edge_devices_dict[edge_device.split('-')[0]]:
                filtered_edge_list.append(edge_device)
        except:
            print("failed to get "+edge_device+" please get this one manually")
            pass
    return filtered_edge_list


def edge_static_routes_audit():
    parser = argparse.ArgumentParser(description='This script will audit all the edges in a region to find the ones that has static route distinguisher')
    parser.add_argument('--region', help='specifiy the region to run the audit for ex: sfo')
    parser.add_argument('--pw', help=argparse.SUPPRESS)
    args = parser.parse_args()

    REGIONS = ['iad', 'pdx', 'bjs', 'fra', 'bom', 'hkg', 'nrt', 'cmh', 'arn', 'dub','syd', 'lhr', 'pek', 'yul', 'kix', 'corp', 'cdg', 'bah', 'zhy', 'sfo','sin', 'icn', 'gru', 'cpt', 'mxp']


    if args.region and args.region in REGIONS:
        edge_list = get_edges(args.region)
        filtered_list = check_edges(edge_list)
        result = check_hercules(filtered_list)
        print_result(result)

    else:
        print("error: invalid region")
        parser.print_help()
        return

if __name__ == "__main__":
	edge_static_routes_audit()
