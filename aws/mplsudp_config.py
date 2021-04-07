#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import (jukebox,nsm,hercules,mcm,bundle_service)
from isd_tools_dev.modules import nsm as nsm1
import collections
import re
import subprocess
import argparse
import sys
import re
import os
import yaml
import jinja2
from time import perf_counter
from jinja2 import Template
import time

'''
This script is used to generate VAR/Conf/Bundles/MCM for MPLSoUDP 

usage: mplsudp_config.py [-h] -d  [...] [-e] [-ca] [-t] [-v]

Script for scaling on vc devices towards border

optional arguments:
  -h, --help            show this help message and exit
  -d  [ ...], --devices  [ ...]
                        DEVICE LIST (EX: "iad6-vc-edg-r1" "iad6-vc-edg-r2"
  -e , --edge_pilot     EDGE PILOT LOOPBACK IP, EX: 54.240.234.212/32
  -ca , --car_pilot     CAR PILOT LOOPBACK IP, EX: 54.240.234.212/32
  -t , --traffic_utilization
                        TRAFFIC UTILIZATION CHECK FOR VC-COR REBASE, EX: 50 -
                        DEFAULTS TO 60
  -v, --variance        VARIANCE TO BE SET FOR VC_BAR REBASE, DEFAULTS TO 10
                        EX: 100

Author  :   anudeept@
Version :   3.5
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
    parser.add_argument('-d','--devices',nargs = '+',metavar='', required = True, help = 'DEVICE LIST (EX: "iad6-vc-edg-r1" "iad6-vc-edg-r2"')
    parser.add_argument("-e","--edge_pilot",type=str, metavar = '', required = False, help = 'EDGE PILOT LOOPBACK IP, EX: 54.240.234.212/32')
    parser.add_argument("-c","--car_pilot",type=str, metavar = '', required = False, help = 'CAR PILOT LOOPBACK IP, EX: 54.240.234.212/32')
    parser.add_argument("-v","--variance",type=str, metavar = '', required = False, help='VARIANCE TO BE SET FOR VC_BAR REBASE, DEFAULTS TO 10 EX: 100')
    parser.add_argument("-i","--ignore_nhs",action="store_true",help="SET THIS TO IGNORE NHS FOR VC-BAR REBASE")
    parser.add_argument("-t","--traffic_utilization",type=str,metavar = '', required = False,help="TRAFFIC UTILIZATION CHECK FOR VC-COR REBASE, EX: 50 - DEFAULTS TO 60")
    return parser.parse_args()

def get_device_regex_site_code(device_list):
    """This is a common function used to get device regex and site code from the list
    of arguments passed

    Args:
        device_list ([type]): list of devices

    Returns:
        device_regex [str]: Device regex from the list of devices ex: iad6-vc-bar(r1|r2|r3)
        site_code [str]: Site code ex: iad6
    """
    contain = collections.defaultdict(list)
    for device in device_list:
        sep = device.rsplit('-', 1)
        contain[sep[0]].append(sep[1])
    regex = ""
    for k,v in contain.items():
        regex = "{}-({})".format(k, '|'.join(v))
    site_list = []
    for device in device_list:
        site_list.append(device.split('-vc')[0])
    site_code = ''.join(list(set(site_list)))
    username = os.getlogin()
    main_path = f'/home/{username}/MPLSoUDP_CONF'
    dir_check = os.path.isdir(main_path)
    if dir_check == True:
        print(bcolors.OKGREEN,f'[Info] : {main_path} directory exists, proceeding')
    else:
        os.mkdir(main_path)
    site_path = f'/home/{username}/MPLSoUDP_CONF/{site_code}'
    print(bcolors.OKBLUE,f'[Info] : Creating {site_path} directory',bcolors.ENDC)
    dir_check = os.path.isdir(site_path)
    if dir_check == True:
        print(bcolors.OKGREEN,f'[Info] : {site_path} directory exists, proceeding')
    else:
        os.mkdir(site_path)
    return regex,site_code

def dry_run_function(bundle_dict: dict):
    """This function is for dry-run, takes dict as argument

    Args:
        bundle_dict (dict): bundle commands dict

    Returns:
        [type]: dry-run result
    """
    #Dry-run section
    bundle_id_dict = {}
    for k,v in bundle_dict.items():
        bundle_id_dict[k] = v.split('bundle-v2/')[-1]
    while True:
        dryrun_input = input('Do you want to  dry-run bundles? yes or no: \n')
        if dryrun_input == "yes":
            break
        elif dryrun_input == "no":
            print(f'[Info]: User selected not to dry-run - skipping')
            break
        else:
            print(f'[Error]: User did not select yes or no (case sensitive)')
    while True:
        if dryrun_input == 'yes' :
            sphere_input = input('Did you check sphere for blocked/restricted days? yes or no : \n')
            if sphere_input == "yes":
                break
            elif sphere_input == "no":
                print(f'[Info]: Dry-run not allowed during blocked/restricted please dry-run later')
                sys.exit()
            else:
                print(f'[Error]: User did not select yes or no')
        else:
            break
            
    dryrun_dict = {}
    dryrun_links = []
    if dryrun_input == 'yes':
        for k,v in bundle_id_dict.items():
            while True:
                user_input = input(f"Do you want to start dry-run for {k}? yes or no: \n")
                if user_input == "yes":
                    sphere_link = bundle_service.get_bundle_dry_run_link(v)
                    print(bcolors.OKBLUE,f'[Info] : Dry-run link for {k}, continue monitoring the Sphere link',bcolors.ENDC)
                    print(f'{sphere_link}')
                    dryrun_dict[k] = sphere_link
                    dryrun_links.append(sphere_link)
                    break
                elif user_input == "no":
                    print(f"User opted not to dry-run for {k}")
                    break
                else:
                    print("User did not select yes or no")
        
    if len(dryrun_links)!=0:
        dryrun_results = "####Dry-run Results:\n{}\n\n".format('\n'.join(dryrun_links))
    else:
        dryrun_results= "####Dry-run Results:\n"
    return dryrun_results

def get_bgp_groups_hercules(device):
    """Function takes device as argument and returns all active bgp groups configured
    on the device via hercules api

    Args:
        device ([str]): device name

    Returns:
        [list]: Returns list of active bgp groups on the device
    """
    try:
        raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    
    external_bgp_groups = []
    # get ebgp peer groups from config
    for line in raw_config:
        if re.match(f"set protocols bgp group .* type external",line):
            group_name = line.split('type')[0].split('group')[1].strip()
            if re.search('(CSC|csc|FAB|fab|BAR|bar)',group_name):
                external_bgp_groups.append(group_name)
    #delete groups which are inactive
    for group in external_bgp_groups:
        for line in raw_config:
            if re.match(f"deactivate protocols bgp group {group}",line):
                external_bgp_groups.remove(group)
    return external_bgp_groups

def mplsudp_mcm_vc_car_rebase(device_list,edg_pilot,car_pilot=None):
    """This function is to create VAR/MCM for VC-CAR MPLSoUDP config

    Args:
        device_list (list): list of vc-car devices
        edg_pilot (str): edg pilot loopback ip which was pre-staged ex: 1.1.1.1/32
        car_pilot (str, optional): CAR pilot route,optional. Defaults to None.
        dxgw_pilot (str, optional): PE pilot route,optional. Defaults to None.
    """
    username = os.getlogin()
    info = get_device_regex_site_code(device_list)
    regex = info[0]
    site_code = info[1]
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)
        local_ae = []
        #get config from hercules
        raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
        for line in raw_config:
            if re.match(f"set interfaces ae.* description .*-(br-tra|vc-cor|vc-dar)-",line):
                if "unit" not in line:
                    ae_num = line.split('description')[0].split('interfaces')[1].strip()
                    local_ae.append(ae_num)
        local_ae_vlan10 = []
        for lag in local_ae:
            for line in raw_config:
                if re.match(f'set interfaces {lag} unit 10 vlan-id 10',line):
                        local_ae_vlan10.append(lag+'.10')
        LOCAL_AE = ','.join(local_ae_vlan10)
        links = jukebox.get_device_link(device)
        upstream_routers = []
        for link_info in links:
            if 'tra' in link_info[0] or 'vc-cor' in link_info[0] or 'vc-dar' in link_info[0]:
                upstream_routers.append(link_info[0])
        UPSTREAM_PEERS = ','.join(upstream_routers)
        border_peers = ['PEER'+str(i) for i in range(1,len(upstream_routers)+1)]
        PEER_DICT = dict(zip(border_peers,upstream_routers))
        PEER_LAG_DICT = {}
        for br_device in upstream_routers:
            device_info = nsm1.get_raw_interfaces_for_device(br_device)
            for i in device_info:
                if device.upper() in i['interface_description']:
                    if 'ae' in i['name']:
                        for k,v in PEER_DICT.items():
                            if br_device == v:
                                PEER_LAG_DICT[k+'_LAG'] = i['name']
        #start var file
        with open(f'{path}/{device}.var','w') as var_file:
            var_file.write(f'IGNORE_ALARMS=Backup RE Active\n')
            var_file.write(f'CAR_PEER_LAGS={LOCAL_AE}\n')
            var_file.write(f'UPSTREAM_PEERS={UPSTREAM_PEERS}\n')
            var_file.write(f'VC_CAR={device}\n')
            for peer in PEER_DICT:
                var_file.write(f'{peer}_ENABLED=true\n')
            for peer,peer_value in PEER_DICT.items():
                var_file.write(f'{peer}={peer_value}\n')
            for peer,peer_lag in PEER_LAG_DICT.items():
                var_file.write(f'{peer}={peer_lag}.10\n')
            var_file.write(f'EDG_PILOT={edg_pilot}\n')
            if car_pilot!=None:
                var_file.write(f'CAR_PILOT_EXISTS=True\n')
                var_file.write(f'CAR_PILOT={car_pilot}\n')
            else:
                var_file.write(f'CAR_PILOT_EXISTS=False\n')
        #MCM Creation
        bundle_commands = []
        bundle_dict = {}
        #/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices phx51-vc-car-r1 --policy vc_car_mplsoudp.yaml --approvers l1-approver l2-approver --policy-args-file vc-car.var -m all.tshifted --tshift
        bundle_command = f'cd {path} &&  /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --modules mplsudp-firewall mplsudp-interfaces mplsudp-policy mplsudp-ebgp-csc mplsudp-routing-options  --stream released --policy vc_car_mplsoudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift'
        bundle_commands.append(bundle_command)
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()

        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[device] = 'https:'+bundle

        print(bcolors.OKGREEN,f'[Info] : Bundles successfully created, waiting for bundles to load - will take about a minute',bcolors.ENDC)
        time.sleep(60)
        for host,bundle in bundle_dict.items():
            print(bcolors.OKGREEN,f'[Info] : {host} - {bundle}',bcolors.ENDC)

        print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
        # x = mcm_creation("mcm_title_overview_vc_car_mplsudp",'iad66-vc-car-r1')
        try:
            mcm_create = mcm.mcm_creation("mcm_title_overview_vc_car_mplsudp",device,site_code)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
        mcm_id = mcm_create[0]
        mcm_overview = mcm_create[2]
        mcm_uid = mcm_create[1]
        mcm_link = 'https://mcm.amazon.com/cms/'+mcm_id
        print(bcolors.OKGREEN,f'[Info] : Successfully created MCM - {mcm_link}',bcolors.ENDC)

        #dry-run steps,deploy commands
        mcm_steps = []
        mcm_bundles = []
        dry_run_commands = []
        deploy_commands = []

        for k,v in bundle_dict.items():
            mcm_bundles.append(f'{k} : {v}')

        step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
        step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
        mcm_steps.append(step_ixops)
        mcm_steps.append(step_netsupport)

        #MCM-steps
        print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
        try:
            for command in bundle_commands:
                device_name = device
                bundle_id = bundle_dict[device_name].split('/')[-1]
                step = {'title':f'Alfred Bundle Deployment for {device_name}','time':45,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
                mcm_steps.append(step)
                dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
                deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : Could not update MCM with steps, exiting',bcolors.ENDC)
            sys.exit()

        #Dry-run section
        dryrun_results = dry_run_function(bundle_dict)

        #Update MCM overview
        print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
        mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
        mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(mcm_bundles))
        mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
        mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
        mcm_overview += dryrun_results
        #MCM Update:
        try:
            mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)

        print(bcolors.OKGREEN,f'[Info] : MCM successfully updated - {mcm_link}',bcolors.ENDC)

def mplsudp_mcm_vc_cir_rebase(device_list,edg_pilot):
    """This function is to create VAR/MCM for VC-CAR MPLSoUDP config

    Args:
        device_list (list): list of vc-cir devices
        edg_pilot (str): edg pilot loopback ip which was pre-staged ex: 1.1.1.1/32
    """
    username = os.getlogin()
    info = get_device_regex_site_code(device_list)
    regex = info[0]
    site_code = info[1]
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)
        local_ae = []
        #start var file
        with open(f'{path}/{device}.var','w') as var_file:
            var_file.write(f'IGNORE_ALARMS=,\n')
            var_file.write(f'EDG_PILOT={edg_pilot}\n')
        #MCM Creation
        bundle_commands = []
        bundle_dict = {}
        #call to get external bgp groups 
        external_bgp_groups = get_bgp_groups_hercules(device)
        for group in external_bgp_groups:
            if re.search('EBGP-BAR',group):
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --modules mplsudp-firewall mplsudp-interfaces mplsudp-policy mplsudp-ebgp-bar mplsudp-routing-options  --stream released --policy vc_cir_mplsoudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift'
            elif re.search('EBGP-FAB',group):
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --modules mplsudp-firewall mplsudp-interfaces mplsudp-policy mplsudp-ebgp-fab mplsudp-routing-options  --stream released --policy vc_cir_mplsoudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift'
        bundle_commands.append(bundle_command) 
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()

        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[device] = 'https:'+bundle

        print(bcolors.OKGREEN,f'[Info] : Bundles successfully created, waiting for bundles to load - will take about a minute',bcolors.ENDC)
        time.sleep(60)
        for host,bundle in bundle_dict.items():
            print(bcolors.OKGREEN,f'[Info] : {host} - {bundle}',bcolors.ENDC)

        print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
        # x = mcm_creation("mcm_title_overview_vc_car_mplsudp",'iad66-vc-cir-r1')
        try:
            mcm_create = mcm.mcm_creation("mcm_title_overview_vc_cir_mplsudp",device,site_code)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
        mcm_id = mcm_create[0]
        mcm_overview = mcm_create[2]
        mcm_uid = mcm_create[1]
        mcm_link = 'https://mcm.amazon.com/cms/'+mcm_id
        print(bcolors.OKGREEN,f'[Info] : Successfully created MCM - {mcm_link}',bcolors.ENDC)

        #dry-run steps,deploy commands
        mcm_steps = []
        mcm_bundles = []
        dry_run_commands = []
        deploy_commands = []

        for k,v in bundle_dict.items():
            mcm_bundles.append(f'{k} : {v}')

        step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
        step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
        mcm_steps.append(step_ixops)
        mcm_steps.append(step_netsupport)

        #MCM-steps
        print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
        try:
            for command in bundle_commands:
                device_name = device
                bundle_id = bundle_dict[device_name].split('/')[-1]
                step = {'title':f'Alfred Bundle Deployment for {device_name}','time':75,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
                mcm_steps.append(step)
                dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
                deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : Could not update MCM with steps, exiting',bcolors.ENDC)
            sys.exit()
        #dry-run results
        dryrun_results = dry_run_function(bundle_dict)
        #Update MCM overview
        print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
        mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
        mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(mcm_bundles))
        mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
        mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
        mcm_overview += dryrun_results
        #MCM Update:
        try:
            mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)

        print(bcolors.OKGREEN,f'[Info] : MCM successfully updated - {mcm_link}',bcolors.ENDC)

def mplsudp_mcm_vc_bar_rebase(device_list,variance=None,ignore_nhs=None):
    """This function will be used to generated MCM/VAR file required to rebase vc-bar devices

    Args:
        device_list ([list]): list of vc_bar devices ex: "iad6-vc-bar-r1" "iad6-vc-bar-r2"
    """
    username = os.getlogin()
    info = get_device_regex_site_code(device_list)
    regex = info[0]
    site_code = info[1]
    #make directory for each device and create VAR file
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)
        with open(f'{path}/{device}.var','w') as var_file:
            var_file.write(f'IGNORE_ALARMS=Multi Protocol Label Switching usage requires a license,BGP Routing Protocol usage requires a license,Rescue configuration is not set\n')
            if variance:
                var_file.write(f'VARIANCE={variance}\n')
            else:
                var_file.write(f'VARIANCE=10\n')
            var_file.write(f'SET_OS=false\n')
            if ignore_nhs:
                if re.search('r1',device):
                    device_name=device.split('-r1')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r2\n')
                elif re.search('r2',device):
                    device_name=device.split('-r2')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r1\n')
                elif re.search('r3',device):
                    device_name=device.split('-r3')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r4\n')
                elif re.search('r4',device):
                    device_name=device.split('-r4')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r3\n')
                elif re.search('r101',device):
                    device_name=device.split('-r101')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r102\n')
                    var_file.write(f'PEER2_ENABLED=True\n')
                    var_file.write(f'PEER2={device_name}'+'-r103\n')
                    var_file.write(f'PEER3_ENABLED=True\n')
                    var_file.write(f'PEER3={device_name}'+'-r104\n')
                elif re.search('r102',device):
                    device_name=device.split('-r102')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r101\n')
                    var_file.write(f'PEER2_ENABLED=True\n')
                    var_file.write(f'PEER2={device_name}'+'-r103\n')
                    var_file.write(f'PEER3_ENABLED=True\n')
                    var_file.write(f'PEER3={device_name}'+'-r104\n')
                elif re.search('r103',device):
                    device_name=device.split('-r103')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r101\n')
                    var_file.write(f'PEER2_ENABLED=True\n')
                    var_file.write(f'PEER2={device_name}'+'-r102\n')
                    var_file.write(f'PEER3_ENABLED=True\n')
                    var_file.write(f'PEER3={device_name}'+'-r104\n')
                elif re.search('r104',device):
                    device_name=device.split('-r104')[0]
                    device_name = str(device_name)
                    var_file.write(f'PEER1_ENABLED=True\n')
                    var_file.write(f'PEER1={device_name}'+'-r101\n')
                    var_file.write(f'PEER2_ENABLED=True\n')
                    var_file.write(f'PEER2={device_name}'+'-r102\n')
                    var_file.write(f'PEER3_ENABLED=True\n')
                    var_file.write(f'PEER3={device_name}'+'-r103\n')

    bundle_commands = []
    bundle_dict = {}
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        if ignore_nhs:
            bundle_command = f'cd {path} &&  /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device}  --policy vc-bar_pre-stage_rebase_ignore_nhs.yaml --policy-args-file {device}.var  --approvers l1-approver -m all --replace-all-config --stream released --preserve-acls --tshift --ignore-network-health-service true'
        else:
            bundle_command = f'cd {path} &&  /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device}  --policy vc-bar_pre-stage_rebase.yaml --policy-args-file {device}.var  --approvers l1-approver -m all --replace-all-config --stream released --preserve-acls --tshift --ignore-network-health-service false'
        bundle_commands.append(bundle_command)
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()

        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[device] = 'https:'+bundle

    print(bcolors.OKGREEN,f'[Info] : Bundles successfully created, waiting for bundles to load - will take about a minute',bcolors.ENDC)
    time.sleep(60)

    for host,bundle in bundle_dict.items():
        print(bcolors.OKGREEN,f'[Info] : {host} - {bundle}',bcolors.ENDC)

    print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
    # x = mcm_creation("mcm_title_overview_prestage_mplsoudp",'iad66-vc-car-r1','iad66')
    if ignore_nhs:
        try:
            mcm_create = mcm.mcm_creation("mcm_title_overview_vc_bar_rebase_ignore_nhs_mplsudp",device_list,regex,site_code)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
    else:
        try:
            mcm_create = mcm.mcm_creation("mcm_title_overview_vc_bar_rebase_mplsudp",device_list,regex,site_code)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = 'https://mcm.amazon.com/cms/'+mcm_id
    print(bcolors.OKGREEN,f'[Info] : Successfully created MCM - {mcm_link}',bcolors.ENDC)

    #dry-run steps,deploy commands
    mcm_steps = []
    mcm_bundles = []
    dry_run_commands = []
    deploy_commands = []

    for k,v in bundle_dict.items():
        mcm_bundles.append(f'{k} : {v}')

    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)

    #MCM-steps
    print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
    try:
        for command in bundle_commands:
            device_name = command.split('--devices')[1].split('--policy')[0].strip()
            bundle_id = bundle_dict[device_name].split('/')[-1]
            step = {'title':f'Alfred Bundle Deployment for {device_name}','time':45,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
            mcm_steps.append(step)
            dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
            deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : Could not update MCM with steps, exiting',bcolors.ENDC)
        sys.exit()
    #dry-run results
    dryrun_results = dry_run_function(bundle_dict)
    #Update MCM overview
    print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
    mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
    mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(mcm_bundles))
    mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
    mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
    mcm_overview += dryrun_results
    #MCM Update:
    try:
        mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)

    print(bcolors.OKGREEN,f'[Info] : MCM successfully updated - {mcm_link}',bcolors.ENDC)

def mplsudp_mcm_vc_cor_rebase(device_list,traffic_utilization=None):
    """This function will be used to generated MCM/VAR file required to rebase vc-cor devices

    Args:
        device_list ([list]): list of vc_cor devices ex: "sea4-vc-cor-b1-r1" "sea4-vc-cor-b1-r2"
    """
    username = os.getlogin()
    info = get_device_regex_site_code(device_list)
    regex = info[0]
    site_code = info[1]
    
    site_regex = [device.split('-r')[0] for device in device_list]
    site_regex = list(set(site_regex))
    device_regex = ''.join(site_regex)
    device_regex = device_regex+'-r[1-4]'
    #make directory for each device and create VAR file
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)
        with open(f'{path}/{device}.var','w') as var_file:
            var_file.write(f'IGNORE_ALARMS=Multi Protocol Label Switching usage requires a license,BGP Routing Protocol usage requires a license,Rescue configuration is not set\n')
            if re.search('r1',device):
                device_name=device.split('-r1')[0]
                device_name = str(device_name)
                var_file.write(f'PEER1={device_name}'+'-r2\n')
                var_file.write(f'PEER2={device_name}'+'-r3\n')
                var_file.write(f'PEER3={device_name}'+'-r4\n')
            elif re.search('r2',device):
                device_name=device.split('-r2')[0]
                device_name = str(device_name)
                var_file.write(f'PEER1={device_name}'+'-r1\n')
                var_file.write(f'PEER2={device_name}'+'-r3\n')
                var_file.write(f'PEER3={device_name}'+'-r4\n')
            elif re.search('r3',device):
                device_name=device.split('-r3')[0]
                device_name = str(device_name)
                var_file.write(f'PEER1={device_name}'+'-r1\n')
                var_file.write(f'PEER2={device_name}'+'-r2\n')
                var_file.write(f'PEER3={device_name}'+'-r4\n')
            elif re.search('r4',device):
                device_name=device.split('-r4')[0]
                device_name = str(device_name)
                var_file.write(f'PEER1={device_name}'+'-r1\n')
                var_file.write(f'PEER2={device_name}'+'-r2\n')
                var_file.write(f'PEER3={device_name}'+'-r3\n')
            var_file.write(f'TRAFFIC_THRESHOLD_ABOVE=100\n')
            if traffic_utilization:
                var_file.write(f'TRAFFIC_UTILIZATION_LEVEL={traffic_utilization}\n')
            else:
                var_file.write(f'TRAFFIC_UTILIZATION_LEVEL=60\n')

    bundle_commands = []
    bundle_dict = {}
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        #/apollo/env/AlfredCLI-2.0/bin/alfred  bundle create --tshift --device-pattern /sea4-vc-cor-b2-r1/ --modules all --policy vc-cor-rebase.yaml --policy-args-file sea4-vc-cor-b2-r1.var --approvers dx-deploy-l1-approver --stream released
        bundle_command = f'cd {path} &&  /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device}  --policy vc-cor-rebase.yaml --policy-args-file {device}.var  --approvers dx-deploy-l1-approver --modules all --replace-all-config --preserve-acls --tshift'
        bundle_commands.append(bundle_command)
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()

        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[device] = 'https:'+bundle

    print(bcolors.OKGREEN,f'[Info] : Bundles successfully created,will take about a minute to load',bcolors.ENDC)
    time.sleep(60)
    for host,bundle in bundle_dict.items():
        print(bcolors.OKGREEN,f'[Info] : {host} - {bundle}',bcolors.ENDC)

    print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
    # x = mcm_creation("mcm_title_overview_prestage_mplsoudp",'iad66-vc-car-r1','iad66')
    try:
        mcm_create = mcm.mcm_creation("mcm_title_overview_vc_cor_rebase_mplsudp",device_list,device_regex,site_code)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = 'https://mcm.amazon.com/cms/'+mcm_id
    print(bcolors.OKGREEN,f'[Info] : Successfully created MCM - {mcm_link}',bcolors.ENDC)

    #dry-run steps,deploy commands
    mcm_steps = []
    mcm_bundles = []
    dry_run_commands = []
    deploy_commands = []

    for k,v in bundle_dict.items():
        mcm_bundles.append(f'{k} : {v}')

    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)

    #MCM-steps
    print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
    try:
        for command in bundle_commands:
            device_name = command.split('--devices')[1].split('--policy')[0].strip()
            bundle_id = bundle_dict[device_name].split('/')[-1]
            step = {'title':f'Alfred Bundle Deployment for {device_name}','time':45,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
            mcm_steps.append(step)
            dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
            deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : Could not update MCM with steps, exiting',bcolors.ENDC)
        sys.exit()
    #dry-run results
    dryrun_results = dry_run_function(bundle_dict)
    #Update MCM overview
    print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
    mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
    mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(mcm_bundles))
    mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
    mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
    mcm_overview += dryrun_results
    #MCM Update:
    try:
        mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
    print(bcolors.OKGREEN,f'[Info] : MCM successfully updated - {mcm_link}',bcolors.ENDC)


def mplsudp_mcm_br_tra_mtu(device_list,nhs_ignore=False):
    """This function will be used to generated MCM/VAR file required to push MTU 
    changes towards br-tra

    Args:
        device_list ([list]): list of vc_bar devices ex: "iad2-br-tra-r7" "iad2-br-tra-r8"
    """
    username = os.getlogin()
    info = get_device_regex_site_code(device_list)
    regex = info[0]
    site_code = info[1]
    #make directory for each device and create VAR file
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)
        lag_list = []
        device_info = nsm1.get_raw_device_with_interfaces(device)
        for info in device_info['interfaces']:
            if re.match('ae.*..10',info['name']):
                lag_list.append(info['name'])
        lags = ','.join(lag_list)
        with open(f'{path}/{device}.var','w') as var_file:
            var_file.write(f'LAGS_TOWARDS_DX_VLAN10={lags}\n')

    bundle_commands = []
    bundle_dict = {}
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        #/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices "iad7-vc-bar-r3" --policy vc_bar_fab_manual_pcn_upgrade_rebase.yaml --policy-args-file test_rebase.var --approvers l1-approver -m all --replace-all-config --preserve-acls --tshift
        bundle_command = f'cd {path} &&  /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device}  --policy vc-bar_pre-stage_rebase.yaml --policy-args-file {device}.var  --approvers l1-approver -m all --replace-all-config --preserve-acls --tshift --ignore-network-health-service false'
        bundle_commands.append(bundle_command)
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()

        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[device] = 'https:'+bundle

    print(bcolors.OKGREEN,f'[Info] : Bundles successfully created',bcolors.ENDC)
    for host,bundle in bundle_dict.items():
        print(bcolors.OKGREEN,f'[Info] : {host} - {bundle}',bcolors.ENDC)

    print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
    # x = mcm_creation("mcm_title_overview_prestage_mplsoudp",'iad66-vc-car-r1','iad66')
    try:
        mcm_create = mcm.mcm_creation("mcm_title_overview_vc_bar_rebase_mplsudp",device_list,regex,site_code)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = 'https://mcm.amazon.com/cms/'+mcm_id
    print(bcolors.OKGREEN,f'[Info] : Successfully created MCM - {mcm_link}',bcolors.ENDC)

    #dry-run steps,deploy commands
    mcm_steps = []
    mcm_bundles = []
    dry_run_commands = []
    deploy_commands = []

    for k,v in bundle_dict.items():
        mcm_bundles.append(f'{k} : {v}')

    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)

    #MCM-steps
    print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
    try:
        for command in bundle_commands:
            device_name = command.split('--devices')[1].split('--policy')[0].strip()
            bundle_id = bundle_dict[device_name].split('/')[-1]
            step = {'title':f'Alfred Bundle Deployment for {device_name}','time':45,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
            mcm_steps.append(step)
            dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
            deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : Could not update MCM with steps, exiting',bcolors.ENDC)
        sys.exit()
    #Update MCM overview
    print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
    mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
    mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(mcm_bundles))
    mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
    mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
    mcm_overview += "####Dry-run Results:\n"
    #MCM Update:
    try:
        mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)

    print(bcolors.OKGREEN,f'[Info] : MCM successfully updated - {mcm_link}',bcolors.ENDC)

def mplsudp_mcm_vc_edg(device_list,car_pilot):
    """This function generates yaml file for a device and renders the yaml file to generate junos config, bundle
    VAR file and MCM

    Args:
        device_list (list): list of devices
        car_pilot (str): car pilot to be used
    """
    username = os.getlogin()
    info = get_device_regex_site_code(device_list)
    regex = info[0]
    site_code = info[1]

    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'

        print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
        dir_check = os.path.isdir(path)
        if dir_check == True:
            print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
        else:
            os.mkdir(path)
            
        with open(f'{path}/{device}.var','w') as var_file:
            var_file.write(f'IGNORE_ALARMS=,\n')
            var_file.write(f'CAR_PILOT={car_pilot}\n')

        print(bcolors.OKGREEN,f'[Info] : Config/VAR file saved to {path}',bcolors.ENDC)
        try:
            raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()


    bundle_commands = []
    bundle_dict = {}
    
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{site_code}/{device}'
        #call to get external bgp groups 
        external_bgp_groups = get_bgp_groups_hercules(device)
        for group in external_bgp_groups:
            if re.search('EBGP-BAR',group):
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --modules mplsudp-firewall mplsudp-interfaces mplsudp-policy mplsudp-ebgp-bar mplsudp-routing-options  --stream released --policy vc_edg_mplsoudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift --ignore-network-health-service false'
            elif re.search('EBGP-CSC',group):
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --modules mplsudp-firewall mplsudp-interfaces mplsudp-policy mplsudp-ebgp-csc mplsudp-routing-options  --stream released --policy vc_edg_mplsoudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift --ignore-network-health-service false'
            elif re.search('EBGP-FAB',group):
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --modules mplsudp-firewall mplsudp-interfaces mplsudp-policy mplsudp-ebgp-fab mplsudp-routing-options  --stream released --policy vc_edg_mplsoudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift --ignore-network-health-service false'
        bundle_commands.append(bundle_command) 
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()

        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[device] = 'https:'+bundle

    print(bcolors.OKGREEN,f'[Info] : Bundles successfully created',bcolors.ENDC)
    for host,bundle in bundle_dict.items():
        print(bcolors.OKGREEN,f'[Info] : {host} - {bundle}',bcolors.ENDC)

    print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
    # x = mcm_creation("mcm_title_overview_mplsudp_vc_edg",'iad66-vc-car-r1','iad66')
    try:
        mcm_create = mcm.mcm_creation("mcm_title_overview_mplsudp_vc_edg",device_list,regex,site_code)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = 'https://mcm.amazon.com/cms/'+mcm_id
    print(bcolors.OKGREEN,f'[Info] : Successfully created MCM - {mcm_link}',bcolors.ENDC)

    #dry-run steps,deploy commands
    mcm_steps = []
    mcm_bundles = []
    dry_run_commands = []
    deploy_commands = []

    for k,v in bundle_dict.items():
        mcm_bundles.append(f'{k} : {v}')

    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)

    #MCM-steps
    print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
    try:
        for device in device_list:
            bundle_id = bundle_dict[device].split('/')[-1]
            step = {'title':f'Alfred Bundle Deployment for {device}','time':75,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
            mcm_steps.append(step)
            dry_run_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -dr -mcm {mcm_id} -b {bundle_id}\n'+'```')
            deploy_commands.append('```\n'+f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy  -mcm {mcm_id} -b {bundle_id}\n'+'```')
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : Could not update MCM with steps, exiting',bcolors.ENDC)
        sys.exit()
    #dry-run results
    dryrun_results = dry_run_function(bundle_dict)
    #Update MCM overview
    print(bcolors.OKBLUE,f'[Info] : Updating MCM overview with deploy/bundle steps',bcolors.ENDC)
    mcm_overview += "####Bundle Generation:\n{}\n\n".format('\n\n'.join(bundle_commands))
    mcm_overview += "####Bundles:\n{}\n\n".format('\n\n'.join(mcm_bundles))
    mcm_overview += "####Dry-run commands:\n{}\n\n".format('\n'.join(dry_run_commands))
    mcm_overview += "####Deploy Bundles:\n{}\n\n".format('\n'.join(deploy_commands))
    mcm_overview += dryrun_results
    #MCM Update:
    try:
        mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)

    print(bcolors.OKGREEN,f'[Info] : MCM successfully updated - {mcm_link}',bcolors.ENDC)

def main():
    start_time = perf_counter()
    args = parse_args()
    device_type = []
    #Validating user arguments
    for device in args.devices:
        device_type.append(re.search(r"(vc|br)-([a-z][a-z][a-z])", device).group())
    device_type = list(set(device_type))
    device_code = ''.join(device_type)
    if device_code == 'vc-edg':
        mplsudp_mcm_vc_edg(args.devices,args.car_pilot)
    elif device_code == 'vc-bar':
        #def mplsudp_mcm_vc_bar_rebase(device_list,variance=None,ignore_nhs=None,peer1=None,peer2=None,peer3=None):
        if args.variance and args.ignore_nhs:
            mplsudp_mcm_vc_bar_rebase(args.devices,variance=args.variance,ignore_nhs=args.ignore_nhs)
        elif args.variance:
            mplsudp_mcm_vc_bar_rebase(args.devices,variance=args.variance)
        elif args.ignore_nhs:
                mplsudp_mcm_vc_bar_rebase(args.devices,ignore_nhs=args.ignore_nhs)
        else:
            mplsudp_mcm_vc_bar_rebase(args.devices)
    elif device_code == 'vc-car':
        #call mplsudp_mcm_vc_car_rebase(device_list,edg_pilot,car_pilot=None)
        if args.car_pilot:
            mplsudp_mcm_vc_car_rebase(args.devices,args.edge_pilot,args.car_pilot)
        else:
            mplsudp_mcm_vc_car_rebase(args.devices,args.edge_pilot)
    elif device_code == 'vc-cor':
        if args.traffic_utilization:
            mplsudp_mcm_vc_cor_rebase(args.devices,args.traffic_utilization)
        else:
            mplsudp_mcm_vc_cor_rebase(args.devices)
    elif device_code == 'vc-cir':
        #call mplsudp_mcm_vc_car_rebase(device_list,edg_pilot,car_pilot=None,dxgw_pilot=None)
        mplsudp_mcm_vc_cir_rebase(args.devices,args.edge_pilot)
    else:
        print(bcolors.FAIL,f'[Error] : Could not find the device type, device type should be car/edg/cir/bar - Exiting',bcolors.ENDC)
        sys.exit()
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
