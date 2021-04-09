#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import mcm
from dxd_tools_dev.modules import jukebox
import argparse
import os
import git
from git import Repo
import sys
import subprocess
from dxd_tools_dev.datastore import ddb
import time
from dxd_tools_dev.modules import (mcm,jukebox,mwinit_cookie,vc_port_alloc,nsm,hercules)
import pandas as pd
import math
import xlwt
import xlrd
import subprocess
import argparse
import string
import sys
import time
import datetime
import re
import os
import yaml
import filecmp
import ipaddress
import requests
import xlrd
from time import perf_counter
from jinja2 import Template

'''
Summary: This script is used to create a maintenance window blocker MCM for VC-CAR.

Adding new line cards work is entirely done from Bladerunner workflow, this MCM is just created for blocking the window and scheduling purposes.

If the new line card is 100G, then this will also create Alfed Bundles.

Once the script is run, user needs to change the time and submit for approval.              

Command to execute the script:

/apollo/env/DXDeploymentTools/bin/linecard_insert_blocker_mcm.py --device "hyd50-vc-car-bom-r1" --slots "7" "2" --card_capacity "100G" --card_type "MPC7E-MRATE"

usage: linecard_insert_blocker_mcm.py [-h]  

Script to add new VC device to JukeBox based on cutsheet provided

optional arguments:
  -h, --help            show this help message and exit
  -d , --device         Name of the device
  -s , --slots          List of slots
  -cap , --card_capacity     Capacity of the slot, 10G or 100G
  --card , --card_type  Card Type, "MPC7E-MRATE" or "MPC-3D-16XGE-SFPP" etc

Version:# 1.0
Author : parayath@                                                                          
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
    parser = argparse.ArgumentParser(description="Script to create MCM for line card installations with Daryl instructions")
    parser.add_argument('-d','--device',type=str, metavar = '', required = True, help = 'Name of the device')
    parser.add_argument('-s','--slots',nargs = '+',metavar='', required = True, help = 'Slots for the device (format : "7" "2"')
    parser.add_argument('-cap','--card_capacity',type=str, metavar = '', required = True, help = 'capacity of the new card (format: "10G" or "100G")')
    parser.add_argument('-card','--card_type',type=str, metavar = '', required = True, help = 'Card Type, "MPC7E-MRATE" or "MPC-3D-16XGE-SFPP" etc')
    return parser.parse_args()

def slot_check(args):
    if "vc-edg" in args.device and args.card_capacity == "100G":
        print(bcolors.FAIL,f"Error >> Currently we don't support 100G line card insertion into 'VC-EDG' devices. Please check with your TPM - exiting",bcolors.ENDC)
        sys.exit()

    print(bcolors.BOLD,"INFO >> Starting device/fpc slot Validation",bcolors.ENDC)
    print(bcolors.OKGREEN,"INFO >> Starting device validation",bcolors.ENDC)
    try:
        device_check = jukebox.get_device_detail(args.device)
    except:
        print(bcolors.FAIL,f"Error >> {args.device} does not exist in JukeBox, please check the arguments provided - exiting",bcolors.ENDC)
        sys.exit()
    
    print(bcolors.OKGREEN,f"INFO >> {args.device} exists in JukeBox, device validation complete",bcolors.ENDC)
    
    print(bcolors.OKBLUE,f"INFO >> Getting Hardware info for {args.device}",bcolors.ENDC)    
    #get dynamo db table
    table = ddb.get_ddb_table("dx_devices_table")    
    device_info = ddb.get_device_from_table(table,"Name",args.device)
    device_model = device_info['Model']
    scb_type = device_info['Hardware']['SCB']['CB 0']

    print(bcolors.OKBLUE,f"INFO >> Starting FPC slot validation checks",bcolors.ENDC)

    fpc_dict = device_info['Hardware']['FPC']
    slots = list(fpc_dict.keys())

    fpc_slots = []
    int_fpc_slots = []

    for fpc in slots:
        fpc_slots.append(fpc.split(' ')[1])
        int_fpc_slots.append(int(fpc.split(' ')[1]))
    
    print(bcolors.OKBLUE,f"INFO >> Checking user passed arg for slots",bcolors.ENDC)

    try:
        int_user_args = [int(slot) for slot in list(args.slots)]
    except:
        print(bcolors.FAIL,"Error >> User arguments for slots is not valid, please check the format passed",bcolors.ENDC)
        print(bcolors.FAIL,"Error >> Run the script with --help for more info",bcolors.ENDC)
        sys.exit()

    if device_model == 'mx960':
        for fpc in int_user_args:
            if fpc not in range(0,12):
                print(bcolors.FAIL,f"Error >> FPC slot {fpc} is not a valid slot for {device_model.upper()} - Exiting",bcolors.ENDC)
                sys.exit()
            else:
                pass
    elif device_model == 'mx480':
        for fpc in int_user_args:
            if fpc not in range(0,8):
                print(bcolors.FAIL,f"Error >> FPC slot {fpc} is not a valid slot for {device_model.upper()} - Exiting",bcolors.ENDC)
                sys.exit()
            else:
                pass
    else:
        print(bcolors.FAIL,f"Error >> {device_model} is not modular and cannot be slotted, please check",bcolors.ENDC)
        sys.exit()
    
    print(bcolors.OKGREEN,f"INFO >> User passed arg for slots is valid",bcolors.ENDC)
    print(bcolors.OKBLUE,f"INFO >> Verifying slot status for {args.device}",bcolors.ENDC)

    for user_arg_slot in args.slots:
        if user_arg_slot not in fpc_slots:
            print(bcolors.OKGREEN,f"INFO >> FPC {user_arg_slot} is not occupied",bcolors.ENDC)
        else:
            print(bcolors.FAIL,f"INFO >> FPC {user_arg_slot} is occupied on {args.device}, exiting",bcolors.ENDC)
            print(bcolors.FAIL,f"INFO >> Check FPC slots at https://dxdeploymenttools.corp.amazon.com/mx_slot_status",bcolors.ENDC)
            sys.exit()

def linecard_mcm(args):
    print(bcolors.BOLD,f"INFO >> Starting MCM creation",bcolors.ENDC)
    site_code = args.device.split('-')[0]
    site_info = jukebox.get_site_region_details(site=site_code)
    region = site_info.region.realm.upper()
    username = os.getlogin()
    device = args.device
    slots = args.slots
    
    num_of_lc = len(args.slots)
    linecard_type = args.card_type

    # Call mcm module to create an MCM with user arrgs
    mcm_info = mcm.mcm_title_overview_linecard_insert_blocker_mcm(args.device,linecard_type,args.slots,num_of_lc,args.card_capacity)
    mcm_overview = mcm_info[1]

    #Create the MCM
    mcm_create = mcm.mcm_creation("mcm_title_overview_linecard_insert_blocker_mcm",args.device,linecard_type,args.slots,num_of_lc,args.card_capacity)
    
    #get mcm id
    mcm_id = mcm_create[0]
    
    #get mcm uid
    mcm_uid = mcm_create[1]
    
    print(bcolors.OKGREEN,f"INFO >> Successfully created MCM - https://mcm.amazon.com/cms/{mcm_id}",bcolors.ENDC)

    if args.card_capacity == "10G" or args.card_capacity == "1G":
        #MCM-steps
        print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
        mcm_steps = []
        mcm_steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
        mcm_steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
        mcm_steps.append({'title':f'Execute Bladerunner workflow','time':300,'description':f'This entire Procedure is executed from the Bladerunner workflow'})
    
        #call function to update MCM
        mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
        print(bcolors.BOLD,f"INFO >> {mcm_id} succesfully updated. Add this MCM Number in Bladerunner execution, in create_mcm section and start Dry-run and Submit for apporvals",bcolors.ENDC)

    elif args.card_capacity == "100G":
        bundle_commands = []
        bundles = []
        dry_run_commands = []
        deploy_commands = []

        path = f'/home/{username}/LINECARD_INSERTION_IN_{device}'
        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)

        for slot in slots:
            print(bcolors.OKBLUE,f'[Info] : Creating CONF file for FPC {slot}',bcolors.ENDC)
            file_conf = path + "/{}-fpc{}.conf".format(device,slot)
            f = open(file_conf, "w")
            f.write("chassis fpc {} {{\n".format(slot))
            f.write("""pic 0 {
            port 2 {
                speed 100g;
            }
            port 5 {
                speed 100g;
            }
        }
        pic 1 {
            port 2 {
                speed 100g;
            }
            port 5 {
                speed 100g;
            }
        }
        }
            """)
            f.close()
            print(f"\n   CONF files created:\n     {file_conf}\n")

            print(bcolors.OKGREEN,f'[Info] : \n   CONF files created:\n     {file_conf}\n',bcolors.ENDC)
            bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --local-files {device}-fpc{slot}.conf --approvers l1-approver --policy vc_car_set_the_chassis_pic_speed_to_100G.yaml --policy-args SLOT={slot}'
            bundle_commands.append(bundle_command)
            print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device} for {slot}',bcolors.ENDC)
            try:
                command_output = subprocess.check_output(bundle_command, shell=True)
            except Exception as error:
                print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
                sys.exit()

            decoded_output = command_output.decode('utf-8').splitlines()
            bundle = decoded_output[-2]
            bundles.append(bundle)
            bundle_id = bundle.split('/')[-1]
            dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
            deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')

            print(bcolors.OKGREEN,f'[Info] : Bundle successfully created',bcolors.ENDC)

            print(bcolors.OKGREEN,f'[Info] : {device} FPC {slot} - {bundle}',bcolors.ENDC)

            print(bcolors.OKGREEN,f'[Info] : All VAR/Conf files saved to {path}',bcolors.ENDC)
        
        #Update MCM-steps
        print(bcolors.OKBLUE,f'[Info] : Adding Alfred Bundle details to MCM Overview',bcolors.ENDC)
        mcm_steps = []
        mcm_steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
        mcm_steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
        mcm_steps.append({'title':f'Execute Bladerunner workflow','time':300,'description':f'This entire Procedure is executed from the Bladerunner workflow'})

        #Update MCM overview
        print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
        mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
        mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(bundles))
        mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
        mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
        mcm_overview += "####Dry-run Results:\n"
        
        #MCM Update:
        try:
            mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)

        print(bcolors.OKGREEN,f"INFO >> MCM Successfully updated - https://mcm.amazon.com/cms/{mcm_id}. Add this MCM Number in Bladerunner execution, in create_mcm section and start Dry-run and Submit for apporvals",bcolors.ENDC)

def main():
    args = parse_args()
    slot_check(args)
    linecard_mcm(args)

if __name__ == "__main__":
    main()
