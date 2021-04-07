#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import sys
import os
import subprocess
import argparse
import collections
from multiprocessing import Pool
from isd_tools_dev.modules import utils
from dxd_tools_dev.modules import nsm


def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='nsm_query.py')
    main_parser.add_argument("-r", "--regex", action="store", dest="regex", required=True, help="Device Regex")
    main_parser.add_argument("-ns", "--nsm-stack", action="store", dest="nsm_stack", help="NSM Stack")
    main_parser.add_argument("-p", "--processes", default=8, type=int, dest="processes", help="No. of processes to run in parallel. Default: 8")
    return main_parser.parse_args()

def tabulate_data(device_data):
    device_table = {'data': "",'headers': ['Device Name', 'Model', 'IP Address', 'OS Version',
            'State'],'align':{'Device Name': {'width': 26, 'just': 'c'},'Model':
                {'width': 26, 'just': 'c'},'IP Address': {'width': 26, 'just': 'c'},'OS Version': {'width': 26, 'just': 'c'},'State': {'width': 26, 'just': 'c'}}}
    for devices in device_data:
        if devices.get():
            utils.nice_table(device_table,[devices.get()['Name'],devices.get()['Model'],devices.get()['IP_Address'],devices.get()['OS'],devices.get()['Life_Cycle_Status']])
    print (device_table['header'])
    print (device_table['data'])

def main():
    cli_arguments = parse_args()
    all_devices = list()
    device_dict = dict()
    if cli_arguments.nsm_stack:
        device_list = nsm.get_devices_from_nsm(cli_arguments.regex,cli_arguments.nsm_stack.lower())
    else:
        device_list = nsm.get_devices_from_nsm(cli_arguments.regex)

    if cli_arguments.processes > 16:
        processes = 16
    else:
        processes = cli_arguments.processes

    pool = Pool(processes)

    for device in device_list:
        all_devices.append(pool.apply_async(nsm.get_device_detail_from_nsm, args = (device, )))

    tabulate_data(all_devices)

if __name__ == '__main__':
    main()
