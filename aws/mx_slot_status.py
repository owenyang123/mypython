#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import sys
import os
import subprocess
import argparse
import collections
import logging
import time
import json

from isd_tools_dev.modules import utils
from dxd_tools_dev.modules import nsm
from dxd_tools_dev.datastore import ddb

logging.basicConfig(level=logging.INFO)

MX480_FPC_SLOTS = ['FPC 0','FPC 1','FPC 2','FPC 3','FPC 4','FPC 5']
MX960_FPC_SLOTS = ['FPC 0','FPC 1','FPC 2','FPC 3','FPC 4','FPC 5','FPC 7','FPC 8','FPC 9','FPC 10','FPC 11']

fpc_state = dict()

table = ddb.get_ddb_table('dx_devices_table')

def get_devices_hardware(device_regex, model):
    device_hardware_dict = dict()
    unfiltered_device_dict = dict()
    complete_regex = device_regex + ' AND model:' + model
    device_names = nsm.get_devices_from_nsm(complete_regex)

    for device in device_names:
        try:
            unfiltered_device_dict.update({device:ddb.get_device_from_table(table,'Name',device)['Hardware']})
        except:
            pass

    for device in unfiltered_device_dict:
        try:
            if unfiltered_device_dict[device]['Chassis'][0] == model:
                device_hardware_dict.update({device:unfiltered_device_dict[device]})
        except:
            pass

    return device_hardware_dict

def get_fpc_status(device_dict):
    device_fpc_status_list = list()
    for device in device_dict:
        if device_dict[device]['Chassis'][0] == 'MX480':
            device_fpc_status_dict = dict()
            available_fpcs = list(set(MX480_FPC_SLOTS) - set(list(device_dict[device]['FPC'].keys())))
            device_fpc_status_dict.update({'Name':device,'Chassis':device_dict[device]['Chassis'],'Occupied FPC Slots':list(device_dict[device]['FPC'].keys()),'Available FPC Slots':available_fpcs,'SCB':device_dict[device]['SCB']})
        elif device_dict[device]['Chassis'][0] == 'MX960':
            device_fpc_status_dict = dict()
            available_fpcs = list(set(MX960_FPC_SLOTS) - set(list(device_dict[device]['FPC'].keys())))
            device_fpc_status_dict.update({'Name':device,'Chassis':device_dict[device]['Chassis'],'Occupied FPC Slots':list(device_dict[device]['FPC'].keys()),'Available FPC Slots':available_fpcs,'SCB':device_dict[device]['SCB']})
        device_fpc_status_list.append(device_fpc_status_dict)

    return device_fpc_status_list

def tabulate_data(device_data):
    device_table = {'data': "",'headers': ['Name', 'Chassis', 'SCB', 'Occupied FPC Slots',
            'Available FPC Slots'],'align':{'Name': {'width': 26, 'just': 'c'},'Chassis':
                {'width': 26, 'just': 'c'},'SCB': {'width': 26, 'just': 'c'},'Occupied FPC Slots': {'width': 26, 'just': 'c'},'Available FPC Slots': {'width': 26, 'just': 'c'}}}
    for devices in device_data:
        utils.nice_table(device_table,[devices['Name'],devices['Chassis'][0],json.dumps(devices['SCB']).strip('{}').replace('"', ''),' '.join(devices['Occupied FPC Slots']),' '.join(devices['Available FPC Slots'])])
    print (device_table['header'])
    print (device_table['data'])

def main():
    fpc_mx960 = get_devices_hardware("name:/.*-vc-(edg|car|agg)-.*/","MX960")
    fpc_mx480 = get_devices_hardware("name:/.*-vc-(edg|car|agg)-.*/","MX480")
    fpc_state = get_fpc_status(fpc_mx960) + get_fpc_status(fpc_mx480)
    tabulate_data(fpc_state)

if __name__ == '__main__':
    main()
