#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import sys
import os
import subprocess
import argparse
import collections
from dxd_tools_dev.modules import nsm
from multiprocessing import Pool
from prettytable import PrettyTable
from dxd_tools_dev.portdata import border as portdata

####################################################################################################
#  Summary: This script is to find all available ports on border routers                           #
#  Usage:                                                                                          #
#  border_port_availability -r <regex>                                                             #
#  border_port_availability -r "fra53-br-agg-r*"                                                   #
#                                                                                                  #
#  Version: 1.0                                                                                    #
#  Author : anudeept@                                                                              #
#  Version: 2.0                                                                                    #            
#  Updated by aaronya@                                                                             #                   
####################################################################################################

# Below two wikis are the references for the port allocations in PTX
#https://w.amazon.com/index.php/Networking/IS/Procedure/Runbook/Backbone%20POPv2(PTX%20BASED)
# https://w.amazon.com/bin/view/Networking/IS/IS-Deployment/Runbooks/BR-AGG-TURNUP/

Ptx_Dx_Allocated_Port_Tra=['et-0/0/37', 'et-0/0/41','et-0/0/43', 'et-0/0/45']
Ptx_Dx_Allocated_Port_Agg=['et-0/0/45', 'et-0/0/46','et-0/0/47', 'et-0/0/48','et-0/0/58','et-0/0/60','et-0/0/61','et-0/0/62']
Ptx_DX_Not_Allocated_Port_Kct=['et-0/0/0','et-0/0/1','et-0/0/2','et-0/0/3','et-0/0/4','et-0/0/5','et-0/0/6','et-0/0/7','et-0/0/8','et-0/0/9','et-0/0/10','et-0/0/11','et-0/0/20','et-0/0/21','et-0/0/24','et-0/0/25','et-0/0/26','et-0/0/27','et-0/0/28','et-0/0/29','et-0/0/30','et-0/0/31','et-0/0/32','et-0/0/33','et-0/0/34','et-0/0/35','et-0/0/71']


def main():
    parser = argparse.ArgumentParser(description="Script to find all available ports on border routers")
    parser.add_argument('-r','--regex', type=str, metavar = '', required = True, help = 'Please type in device regex such as fra53-br-agg-r*')

    args = parser.parse_args()
    return(available_border_port(args))


def available_border_port(args):
    border_device_list=sorted(nsm.get_devices_from_nsm(args.regex))
    Free_Border_Port_For_DX=[]
    for device in border_device_list:
        device_information = portdata.get_full_device_info(device)
        print("\n")
        print(device_information['device_name'],device_information['model'],device_information['os_version'])
        if 'ptx' in device_information['model'] and 'br-tra' in device_information['device_name']:
            for port,port_info in sorted(device_information['ports'].items()):
                if port_info['availability_state'].split(":")[0] == 'AVAILABLE':
                    Free_Border_Port_For_DX.append(port)
                    if port.split(":")[0] in Ptx_Dx_Allocated_Port_Tra:
                        Allocated_In_Guideline="Dx Port"
                    else:
                        Allocated_In_Guideline="Non DX Port"
                    if port_info['availability_state'] != 'AVAILABLE:not_in_nsm':
                        print(f"{port}  {port_info['admin_status']} {port_info['status']} description: {port_info['description']} port_speed(G): {str(int(int(port_info['bandwidth_mbit'])/1000))} {Allocated_In_Guideline}")
                    elif port_info['availability_state'] == 'AVAILABLE:not_in_nsm':
                        print(f"{port}  OPTIC NOT PRESENT  {Allocated_In_Guideline}")
        elif 'ptx' in device_information['model'] and 'br-agg' in device_information['device_name']:
            for port,port_info in sorted(device_information['ports'].items()):
                if port_info['availability_state'].split(":")[0] == 'AVAILABLE':
                    Free_Border_Port_For_DX.append(port)
                    if port.split(":")[0] in Ptx_Dx_Allocated_Port_Agg:
                        Allocated_In_Guideline="Dx Port"
                    else:
                        Allocated_In_Guideline="Non Dx Port"
                    if port_info['availability_state'] != 'AVAILABLE:not_in_nsm':
                        print(f"{port}  {port_info['admin_status']} {port_info['status']} description: {port_info['description']} port_speed(G): {str(int(int(port_info['bandwidth_mbit'])/1000))} {Allocated_In_Guideline}")
                    elif port_info['availability_state'] == 'AVAILABLE:not_in_nsm':
                        print(f"{port}  OPTIC NOT PRESENT  {Allocated_In_Guideline}")
        elif 'ptx' in device_information['model'] and 'br-kct' in device_information['device_name']:
            for port,port_info in sorted(device_information['ports'].items()):
                if port_info['availability_state'].split(":")[0] == 'AVAILABLE':
                    Free_Border_Port_For_DX.append(port)
                    if port.split(":")[0] in Ptx_DX_Not_Allocated_Port_Kct:
                        Allocated_In_Guideline="Non Dx Port"
                    else:
                        Allocated_In_Guideline="Free to pick"
                    if port_info['availability_state'] != 'AVAILABLE:not_in_nsm':
                        print(f"{port}  {port_info['admin_status']} {port_info['status']} description: {port_info['description']} port_speed(G): {str(int(int(port_info['bandwidth_mbit'])/1000))} {Allocated_In_Guideline}")
                    elif port_info['availability_state'] == 'AVAILABLE:not_in_nsm':
                        print(f"{port}  OPTIC NOT PRESENT  {Allocated_In_Guideline}")
        else:
            for port,port_info in sorted(device_information['ports'].items()):
                if port_info['availability_state'].split(":")[0] == 'AVAILABLE':
                    Free_Border_Port_For_DX.append(port)
                    Allocated_In_Guideline="free to pick"
                    if port_info['availability_state'] != 'AVAILABLE:not_in_nsm':
                        print(f"{port}  {port_info['admin_status']} {port_info['status']} description: {port_info['description']} port_speed(G): {str(int(int(port_info['bandwidth_mbit'])/1000))} {Allocated_In_Guideline}")
                    elif port_info['availability_state'] == 'AVAILABLE:not_in_nsm':
                        print(f"{port}  OPTIC NOT PRESENT  {Allocated_In_Guideline}")

    return Free_Border_Port_For_DX


if __name__ == "__main__":
   main()