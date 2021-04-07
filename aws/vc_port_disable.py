#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import (mcm,jukebox,mwinit_cookie,vc_port_alloc,nsm,hercules)
import pandas as pd
import argparse
import string
import sys
import os
from jinja2 import Template
from pathlib import Path

"""
This script is intended to generate local config file to disable ports on -VC-
devices. 
This config file can be used with
https://code.amazon.com/packages/NetEngAutoChecksPolicies/blobs/mainline/--/configuration/etc/neteng_autochecks_policies/vc_disable_physical_interfaces.yaml
to generate Alfred bundles for disabling interfaces on DX devices. 
Version 1: It reads input CSV cutsheet, parses -vc- devices and associated
interfaces and generates local config files per -vc- device  in home directory. 
"""

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

parser = argparse.ArgumentParser(description="Script to generate Local Config file to shut/unshut  ports on -VC- Device", add_help=True)
parser.add_argument("--f", "--file", help = "Input CSV file for disabling ports", type=str, required=True)
parser.add_argument("--s", "--shut", help = "Pass this argument to shut the interfaces on VC Devices from cutsheet", action="store_true")
parser.add_argument("--u", "--unshut", help = "Pass this argument to unshut the interfaces on VC Devices from cutsheet", action="store_true")

args =  parser.parse_args()
username = os.getlogin()
it = "interfaces {"
clit = "\n }"
cutsheet_loc = args.f

if len(cutsheet_loc)!= 0:
    df = pd.read_csv(cutsheet_loc)
else:
    print(bcolors.FAIL,f'Error >> No cutsheet found, please verify the path',bcolors.ENDC)
    sys.exit()

try:
    print(bcolors.OKBLUE,f'Trying to fetch a_hostname and z_hostname from cutsheet',bcolors.ENDC)
    device_list_a = df['a_hostname']
    device_list_z = df['z_hostname']
except:
    print(bcolors.FAIL,f'Error >> Could not find columns a_hostname and z_hostname in the custsheet',bcolors.ENDC)
    sys.exit()

a_hosts = []
z_hosts = []
intf_vc_a = []
intf_vc_z = []

for dev in device_list_a:
    if 'vc' in dev:
        a_hosts = list (df.a_hostname.unique())
    else:
        print(bcolors.WARNING,f'A side is not VC device, Skipping',bcolors.ENDC)
        break
for dev in device_list_z:
    if 'vc' in dev:
        z_hosts = list (df.z_hostname.unique())
    else:
        print(bcolors.WARNING,f'Z side is not VC device, Skipping',bcolors.ENDC)
        break

if len(a_hosts) != 0:
    for device in a_hosts:
        df_new_a = df[df['a_hostname'] == device]
        try:
            intf_vc_a = list(df_new_a['a_interface'])
            if len(intf_vc_a) != 0:
                print(bcolors.OKBLUE,f'Creating Config file for {device}',bcolors.ENDC)
                file_path = f'/home/{username}/{device}.conf'
                f = open(file_path, "w")
                f.write(it)
                if args.s:
                    for x in intf_vc_a:
                        tm1 = Template ("\n \t {{intf}} { \n \t disable; \n \t }")
                        intf_config = tm1.render(intf=x)
                        f.writelines(intf_config)
                    f.write(clit)
                    f.close()
                elif args.u:
                    for x in intf_vc_a:
                        tm1 = Template ("\n \t {{intf}} { \n \t delete: disable; \n \t }")
                        intf_config = tm1.render(intf=x)
                        f.writelines(intf_config)
                    f.write(clit)
                    f.close()
                else:
                    print(bcolors.FAIL,f'Error >> Could not find argument to Shut or Unshut interfaces',bcolors.ENDC)
                    sys.exit()
                print(bcolors.HEADER,f'Config file /home/{username}/{device}.conf is created',bcolors.ENDC)
            else:
                print(bcolors.WARNING,f'No interfaces found for device {device}, No config to generate',bcolors.ENDC)
        except (KeyError):
            print(bcolors.FAIL,f'Error >> Column a_interface not found',bcolors.ENDC)
else:
    print(bcolors.WARNING,f'A side is not VC device, Skipping',bcolors.ENDC)

if len(z_hosts) != 0:
    for host in z_hosts:
        df_new_z = df[df['z_hostname'] == host]
        try:
            intf_vc_z = list(df_new_z['z_interface'])
            if len(intf_vc_z) != 0:
                print(bcolors.OKBLUE,f'Creating Config file for {host}',bcolors.ENDC)
                file_path = f'/home/{username}/{host}.conf'
                f = open(file_path, "w")
                f.write(it)
                if args.s:
                    for x in intf_vc_z:
                        tm1 = Template ("\n \t {{intf}} { \n \t disable; \n \t }")
                        intf_config = tm1.render(intf=x)
                        f.writelines(intf_config)
                    f.write(clit)
                    f.close()
                elif args.u:
                    for x in intf_vc_z:
                        tm1 = Template ("\n \t {{intf}} { \n \t delete: disable; \n \t }")
                        intf_config = tm1.render(intf=x)
                        f.writelines(intf_config)
                    f.write(clit)
                    f.close()
                else:
                    print(bcolors.FAIL,f'Error >> Could not find argument to Shut or Unshut interfaces',bcolors.ENDC)
                    sys.exit()
                print(bcolors.HEADER,f'Config file /home/{username}/{host}.conf is created',bcolors.ENDC)
            else:
                print(bcolors.WARNING,f'No interfaces found for device {host}, No config to generate',bcolors.ENDC)
        except (KeyError):
            print(bcolors.FAIL,f'Error >> Column z_interface not found',bcolors.ENDC)
else:
    print(bcolors.WARNING,f'Z side is not VC device, Skipping',bcolors.ENDC)
