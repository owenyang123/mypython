#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
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

"""
This script is used to create VAR/CONF/BUNDLES/MCM for scaling vc devices

Usage wiki : https://w.amazon.com/bin/view/DXDEPLOY_Automation_Others/Scripts/vc_scaling
Author : anudeept@
version : 1.1
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

def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Script for scaling on vc devices towards border")
    parser.add_argument('-m','--cutsheet_mcm', type=str, metavar = '', required= True, help = 'BORDER-TRA VC-CAR SCALING CUTSHEET MCM NUMBER, EX: MCM-1234')
    parser.add_argument("-e","--existing_lag",action="store_true",help="OPTION TO ADD LINKS TO EXISTING LAG")
    parser.add_argument("-n","--new_lag",action="store_true",help="OPTION TO ADD LINKS TO NEW LAG")
    parser.add_argument("-b","--bundle_only",action="store_true",help="CREATE ONLY BUNDLES")
    return parser.parse_args()

def get_site_code_regex(vc_car_list : list,br_tra_list : list) -> str:
    """
    This function generates site code, device regex required for MCM

    Args:
        vc_car_list (list): List of vc devices
        br_tra_list (list): List of border tra devices

    Returns:
        [vc_site_code -> str]: vc site code (ex: sfo20)
        [br_site_code -> str]: br site code (ex: sfo5)
        [vc_device_regex -> str]: vc device regex (ex: sfo5-vc-car-(r1|r2))
        [br_device_regex -> str]: br device regex (ex: sfo5-br-tra-(r1|r2))
        [path -> str]: Path directory for storing var/conf files
        [username -> str]: username
    """    
    username = os.getlogin()
    #get vc site code 'sfo20'
    site_info = [device.split('-')[0] for device in vc_car_list]
    site_info = set(site_info)
    vc_site_code = ''
    for info in site_info:
        vc_site_code = vc_site_code + info
    vc_site_code = vc_site_code.upper()
    #get br site code ex: 'sfo5'
    br_info = [device.split('-')[0] for device in br_tra_list]
    br_info = set(br_info)
    br_site_code = ''
    for info in br_info:
        br_site_code += info
    br_site_code = br_site_code.upper()
    #get vc/br device regex
    vc_regex_maker = [device.split('-')[-1] for device in vc_car_list]
    vc_regex_routers = '|'.join(vc_regex_maker)
    vc_regex = set([device.split('-r')[0] for device in vc_car_list])
    vc_regex = list(vc_regex)
    vc_device_regex = ''.join(vc_regex)+'-('+ vc_regex_routers +')'

    br_regex_maker = [device.split('-')[-1] for device in br_tra_list]
    br_regex_routers = '|'.join(br_regex_maker)
    br_regex = set([device.split('-r')[0] for device in br_tra_list])
    br_regex = list(br_regex)
    br_device_regex = ''.join(br_regex)+'-('+ br_regex_routers +')'
    #path 
    path = f'/home/{username}/SCALING_{vc_site_code}_CAR_{br_site_code}_TRA'
    
    #Get local_core for regiion
    cor_regex="name:/{}.*br-cor-r.*/".format(br_site_code.lower())
    try:
        border_core_devices=sorted(nsm.get_devices_from_nsm(cor_regex))
        br_cor = border_core_devices[0]
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : Could not find br-cor for {br_site_code}',bcolors.ENDC)
        sys.exit()
    
    return vc_site_code,br_site_code,vc_device_regex,br_device_regex,path,username,br_cor

def read_cutsheet_car_tra(cutsheet_mcm : str):
    """This function reads scaling cutsheet and returns pandas data frame 
    and list of vc and br devices

    Args:
        cutsheet (excel sheet): Path to cutsheet

    Returns:
        df (pandas data frame): Pandas data frame with all cabling info
        a_device_list -> list: List of a side devices
        z_device_list -> list: List of z side devices
    """
    #download cutsheet from mcm.py module
    try:
        cutsheet = mcm.download_latest_cutsheet(cutsheet_mcm)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    
    #read cutsheet
    df = pd.read_excel(cutsheet,engine="xlrd",sheet_name=None)
    df_new = pd.DataFrame()

    if len(df) != 0:
        for info in df.items():
            df_new = df_new.append(info[1])
    else:
        print(bcolors.FAIL,f'Error >> Excel sheet is not in the right format, please verify',bcolors.ENDC)
        sys.exit()

    try:
        df_new = df_new[['a_hostname','a_interface','a_lag','z_hostname','z_interface','z_lag']]
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    
    #strip whitespaces in all columns 
    df_new[df_new.columns] = df_new.apply(lambda x: x.str.strip())
    
    expected_columns = ['a_hostname', 'a_interface', 'a_lag', 'z_hostname', 'z_interface', 'z_lag']
    columns_cutsheet = list(df_new.columns)
    
    if expected_columns == columns_cutsheet:
        print(bcolors.OKGREEN,f'[Info] : Cutsheet has the expected columns, proceeding',bcolors.ENDC)
    else:
        print(bcolors.FAIL,f'[Error] : Expected columns not found in cutsheet, exiting',bcolors.ENDC)
        sys.exit()

    a_devices = list(df_new['a_hostname'].unique())
    z_devices = list(df_new['z_hostname'].unique())

    #get list of vc devices
    device_list = []
    for device in a_devices:
        device_reg = re.search(r"vc-([a-z][a-z][a-z])-", device)
        if device_reg != None and device_reg.group(1) == 'car':
            device_list.append(device)

    for device in z_devices:
        device_reg = re.search(r"vc-([a-z][a-z][a-z])-", device)
        if device_reg != None and device_reg.group(1) == 'car':
            device_list.append(device)


    if device_list != []:
        print(bcolors.OKGREEN,f'[Info] : Found {device_list} in cutsheet',bcolors.ENDC)
    else:
        print(bcolors.FAIL,f'[Error] : No vc-car devices found in cutsheet',bcolors.ENDC)
        sys.exit()
    
    df_final = pd.DataFrame()
    for hostname in device_list:
        df_a = df_new[df_new['a_hostname'] == hostname]
        df_z = df_new[df_new['z_hostname'] == hostname]
        df_z = df_z.rename(columns={'a_hostname': 'z_hostname', 'a_interface': 'z_interface','a_lag': 'z_lag','z_hostname': 'a_hostname','z_interface': 'a_interface','z_lag':'a_lag'})
        df_z = df_z[['a_hostname','a_interface','a_lag','z_hostname','z_interface','z_lag']]
        df_final = df_final.append(df_a.append(df_z,ignore_index=True))

    #get list of vc-car/br-tra
    a_list = list(df_final['a_hostname'].unique())
    z_list = list(df_final['z_hostname'].unique())
    
    a_device_list = [device.strip() for device in a_list]
    z_device_list = [device.strip() for device in z_list]
    
    return df_final,a_device_list,z_device_list

def car_tra_bundle_existing_lag(df,vc_car_list,br_tra_list):
    """
    This function loops over data from car_tra_read_cr function and returns alfred bundles and 
    saves VAR/Conf files needed

    Args:
        df (pandas data frame)
        vc_car_list (list) 
        br_tra_list (list)

    Returns:
        bundle_dict [dictionary]: key - vc device, value - bundle
        bundle_commands [list] : List of bundle commands needed for MCM
        vc_site_code [str]: site code for vc device 
        vc_device_regex [str]: device regex for vc devices
        br_device_regex [str]: device regex for br devices    
    """
    df_new = df
    vc_car_list = vc_car_list
    br_tra_list = br_tra_list
    username = os.getlogin()
    bundle_commands = []
    bundle_dict = {}

    site_data = get_site_code_regex(vc_car_list,br_tra_list)
    #get vc site code 'sfo20'
    vc_site_code = site_data[0].upper()
    #get br site code
    br_site_code = site_data[1].upper()
    #device regex
    vc_device_regex = site_data[2]
    br_device_regex = site_data[3]
    path = site_data[4]
    path = f'/home/{username}/SCALING_{vc_site_code}_CAR_{br_site_code}_TRA'
    print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
    dir_check = os.path.isdir(path)
    if dir_check == True:
        print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
    else:
        os.mkdir(path)
    #Loop over vc device list
    for vc_device in vc_car_list:
        df_vc = df_new[df_new['a_hostname'] == vc_device ]
        VC_CAR_AE_LIST = list(df_vc['a_lag'].unique())
        BR_TRA_LIST = list(df_vc['z_hostname'].unique())
        print(bcolors.HEADER,f'[Info] : Creating VAR/CONF/Bundles for {vc_device}',bcolors.ENDC)
        VC_CAR_INTF_DICT = {}
        VC_CAR_INTF_DICT['interfaces'] = {}

        EXISTING_LAGS = ','.join(VC_CAR_AE_LIST)
        print(bcolors.OKBLUE,f'[Info] : Creating mapping between {vc_device} and {BR_TRA_LIST}',bcolors.ENDC)

        #get main dict for mapping interfaces
        for indx,series in df_vc.iterrows():
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']] = {}
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['a_lag'] = series['a_lag']
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['z_hostname'] = series['z_hostname']
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['z_interface'] = series['z_interface']
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['z_lag'] = series['z_lag']

        # Maps lag to ae --> {'LAG1':{'ae24': [],'LAG2': {'ae25':[]}}
        VC_CAR_LAG_NUM = ['LAG_'+str(count) for count in range(1,len(VC_CAR_AE_LIST)+1)]
        VC_CAR_LAG_DICT = {}
        for lag_num,ae_num in dict(zip(VC_CAR_LAG_NUM,VC_CAR_AE_LIST)).items():
            VC_CAR_LAG_DICT[lag_num] = {}
            VC_CAR_LAG_DICT[lag_num][ae_num] = []
        
        #Appends interfaces to VC_CAR_LAG_DICT 
        for device,intf in VC_CAR_INTF_DICT.items():
            for interface,params in intf.items():
                for lag_num,ae_num in VC_CAR_LAG_DICT.items():
                    for ae,intfs in ae_num.items():
                        if ae == params['a_lag']:
                            intfs.append(interface)
        
        #LAG1,LAG2 interfaces dict --> {'LAG_1_INTERFACES': {'ae24': ['xe-1/1/1','xe-2/2/2']}}
        VC_CAR_LAG_INT_DICT = {}
        VC_CAR_LAG_INT_DICT = {k+'_INTERFACES' : v for k,v in VC_CAR_LAG_DICT.items()}

        #LLDP INFO FOR VAR FILE
        LLDP_INFO = []
        for indx,series in df_vc.iterrows():
            #xe-5/3/1:sfo5-br-tra-r7_et-0/0/68:2
            LLDP_INFO.append(series['a_interface']+':'+series['z_hostname']+'_'+series['z_interface'])
        LLDP_INFO = ','.join(LLDP_INFO)

        #BR_TRA PEER {'PEER_1': 'sfo5-bt-tra-r7','PEER_2':'sfo5-br-tra-r8'} 
        BR_PEER_LIST = ['PEER_'+str(i) for i in range(1,len(BR_TRA_LIST)+1)]
        BR_PEER_DICT = dict(zip(BR_PEER_LIST,BR_TRA_LIST))
        BR_PEER_DICT = {}
        for peer,br_device in dict(zip(BR_PEER_LIST,BR_TRA_LIST)).items():
            BR_PEER_DICT[peer] = {}
            BR_PEER_DICT[peer][br_device] = []

        #BR_TRA PEER INTF DICT {'PEER_1_INTERFACES': 'sfo5-bt-tra-r7','PEER_2_INTERFACES' :'sfo5-br-tra-r8'}
        BR_PEER_INT_DICT = {peer+'_INTERFACES' : br_device for peer,br_device in BR_PEER_DICT.items()}


        #PEER INT INFO - {'PEER_1_LAG': {'sfo5-br-tra-r1': ['xe-0/0/0','xe-1/1/1']}}
        AE_MAPPING = {}
        BR_PEER_INT_LIST = ['PEER_'+str(i)+'_INTERFACES' for i in range(1,len(BR_TRA_LIST)+1)]
        BR_PEER_INT_DICT = {}
        for peer,br_device in dict(zip(BR_PEER_INT_LIST,BR_TRA_LIST)).items():
            BR_PEER_INT_DICT[peer] = {}
            BR_PEER_INT_DICT[peer][br_device] = []       

        for br_device in BR_TRA_LIST:
            df_br = df_vc[df_vc['z_hostname'] == br_device]
            for indx,series in df_br.iterrows():
                if br_device == series['z_hostname']:
                    AE_MAPPING[series['a_lag']] = series['z_lag']
            for peer_int,br_device in BR_PEER_INT_DICT.items():
                for device,rem_intf in br_device.items():
                    for indx,series in df_br.iterrows():
                        if device == series['z_hostname']:
                            rem_intf.append(series['z_interface'])

        # PEER LAG INFO --> {'PEER_1_LAG': 'ae104', 'PEER_2_LAG': 'ae104'}
        BR_PEER_LAG_LIST = ['PEER_'+str(count)+'_LAG' for count in range(1,len(AE_MAPPING)+1)]
        BR_PEER_LAG_DICT = {}
        for k,v in AE_MAPPING.items():
            for peer in BR_PEER_LAG_LIST:
                BR_PEER_LAG_DICT[peer] = v
        
        print(bcolors.OKGREEN,f'[Info] : Successfully mapped {vc_device} to {BR_TRA_LIST}',bcolors.ENDC)
        #Create VAR FILE to /home/anudeept/SCALING_SFO20_SFO5/sfo5-br-tra-r7.var
        with open(f'{path}/{vc_device}.var','w') as var_file:
            var_file.write(f'ADD_LINKS_TO_EXISTING_LAG=True\n')
            var_file.write(f'EXISTING_LAGS ={EXISTING_LAGS}\n')
            var_file.write(f'IGNORE_ALARMS=,\n')
            var_file.write(f'INF_LIGHT_THRESHOLD_HIGH=1\n')
            var_file.write(f'INF_LIGHT_THRESHOLD_LOW=-10\n')
            for lag_num,ae_num in VC_CAR_LAG_DICT.items():
                for ae,intfs in ae_num.items():
                    var_file.write(f'{lag_num}={ae}\n')
            for lag_intf,ae_num in VC_CAR_LAG_INT_DICT.items():
                for ae,intfs in ae_num.items():
                    intfs = ','.join(intfs)
                    var_file.write(f'{lag_intf}={intfs}\n')
            var_file.write(f'LLDP_NEIGHBORS_INFO={LLDP_INFO}\n')
            for peer,br_device in BR_PEER_DICT.items():
                for device,intfs in br_device.items():
                    var_file.write(f'{peer}={device}\n')
            for peer_intf,br_device in BR_PEER_INT_DICT.items():
                for device,rem_inf in br_device.items():
                    rem_inf = ','.join(rem_inf)
                    var_file.write(f'{peer_intf}={rem_inf}\n')
            for peer_lag,lag_num in BR_PEER_LAG_DICT.items():
                var_file.write(f'{peer_lag}={lag_num}\n')
            for k in VC_CAR_LAG_DICT:
                if 'LAG_2' in k:
                    var_file.write(f'ENABLE_LAG_2_CHECKS=true\n')
                if 'LAG_3' in k:
                    var_file.write(f'ENABLE_LAG_3_CHECKS=true\n')
                if 'LAG_4' in k:
                    var_file.write(f'ENABLE_LAG_4_CHECKS=true\n')
            for k in BR_PEER_DICT:
                if 'PEER_2' in k:
                    var_file.write(f'ENABLE_PEER_2_CHECKS=true\n')
                if 'PEER_3' in k:
                    var_file.write(f'ENABLE_PEER_3_CHECKS=true\n')
                if 'PEER_4' in k:
                    var_file.write(f'ENABLE_PEER_4_CHECKS=true\n')

        print(bcolors.OKGREEN,f'[Info] : Sucessfully created VAR file for {vc_device}',bcolors.ENDC)
        print(bcolors.OKBLUE,f'[Info] : Creating yaml file for {vc_device}',bcolors.ENDC)
        #create yaml file
        try:
            with open(f'{path}/{vc_device}.yaml','w') as outfile:
                outfile.write(yaml.dump(VC_CAR_INTF_DICT,default_flow_style=False ))
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
        
        #load yaml file
        try:
            yaml_file = yaml.safe_load(open(f'{path}/{vc_device}.yaml'))
        except FileNotFoundError as error:
            print(bcolors.FAIL,f'[Error] : Could not load yaml file',bcolors.ENDC)
            sys.exit()

        print(bcolors.OKGREEN,f'[Info] : Successfully created yaml file for {vc_device}',bcolors.ENDC)

        print(bcolors.OKBLUE,f'[Info] : Creating conf file for {vc_device}',bcolors.ENDC)

        #template for creating config
        j2_template = Template(
        '''
        interfaces {
            {% for intf,params in interfaces.items() -%}
                replace: {{intf}} {
                description "{{params.z_hostname}} {{params.z_interface}} via {{params.a_lag}}";
                gigether-options {
                    802.3ad {{params.a_lag}};
                }
                }
            {% endfor %}
        }
        '''
        )
        #create config
        try:
            with open(f'{path}/{vc_device}.conf','w') as device_config:
                print(j2_template.render(yaml_file),file=device_config)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
        
        print(bcolors.OKGREEN,f'[Info] : Successfully created Conf file for {vc_device}',bcolors.ENDC)
        bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {vc_device} --local-files {vc_device}.conf --policy add_links_to_lag_between_vc-car_and_br-tra.yaml --policy-args-file {vc_device}.var  --approvers l1-approver'
        bundle_commands.append(bundle_command)
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {vc_device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()
            
        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[vc_device] = 'https:'+bundle
    
    for device,bundle in bundle_dict.items():
        print(bcolors.OKGREEN,f'[Info] : Bundles successfully created',bcolors.ENDC)
        print(bcolors.OKGREEN,f'[Info] : {device} - {bundle}',bcolors.ENDC)
    print(bcolors.OKGREEN,f'[Info] : All VAR/Conf files saved to {path}',bcolors.ENDC)
    return bundle_dict,bundle_commands,vc_site_code,vc_car_list,vc_device_regex,br_device_regex

def car_tra_mcm_existing_lag(df,vc_car_list,br_tra_list):
    """
    This function creates MCM for CAR-TRA Scaling

    Args:
        args (args): site code,vc device list, vc device regex, br device regex, gb cr
    """    
    mcm_data = car_tra_bundle_existing_lag(df,vc_car_list,br_tra_list)
    bundle_dict = mcm_data[0]
    bundle_commands = mcm_data[1]
    site_code = mcm_data[2]
    device_list = mcm_data[3]
    vc_device_regex = mcm_data[4]
    br_device_regex = mcm_data[5]
    gb_cr = 'CR-1234'
    print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
    # function from mcm.py -  mcm_create = mcm_creation("mcm_title_overview_link_add_existing_lag",'sfo20',['sfo20-vc-car-r1','sfo20-vc-car-r2'],vc_device_regex,br_device_regex,'CR-1234')
    try:
        mcm_create = mcm.mcm_creation("mcm_title_overview_link_add_existing_lag",site_code,device_list,vc_device_regex,br_device_regex,gb_cr)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
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
    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)
    for k,v in bundle_dict.items():
        mcm_bundles.append(f'{k} : {v}')
    
    #MCM-steps
    print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
    try:
        for command in bundle_commands:
            device_name = command.split('--devices')[1].split('--local-files')[0].strip()
            bundle_id = bundle_dict[device_name].split('/')[-1]
            step = {'title':f'Alfred Bundle Deployment for {device_name}','time':60,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
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

#New LAG
def car_tra_bundle_new_lag(df,vc_car_list,br_tra_list):
    """This function will be called by Muda and generates VAR/Conf/Bundle needed for new lag MCM
    
    ex: create_var_bundle_new_lag('syd4_border_scaling.xlsx','syd1-br-cor-r1')

    Args:
        cutsheet (excel sheet): Pass in the cutsheet with full path
        local_cor (str): Local cor in the region, ex: 'syd1-br-cor-r1'
        ipv4_prefix_list (list): list of inet+csc border ip's
        ipv6_prefix_list (list), optional): List of v6 border prefixes. Defaults to None.
    """    
    df_final = df
    vc_car_list = vc_car_list
    br_tra_list = br_tra_list
    username = os.getlogin()
    bundle_commands = []
    bundle_dict = {}

    site_data = get_site_code_regex(vc_car_list,br_tra_list)
    #get vc site code 'sfo20'
    vc_site_code = site_data[0].upper()
    #get br site code
    br_site_code = site_data[1].upper()
    #device regex
    vc_device_regex = site_data[2]
    br_device_regex = site_data[3]
    br_cor = site_data[6]
    br_cor = ''.join(br_cor)
    path = f'/home/{username}/SCALING_{vc_site_code}_CAR_{br_site_code}_TRA_NEW_LAG'
    print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
    dir_check = os.path.isdir(path)
    if dir_check == True:
        print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
    else:
        os.mkdir(path)
    
    #Loop over vc_car list and to create VAR/CONF/BUNDLES
    for vc_device in vc_car_list:
        df_vc = df_final[df_final['a_hostname'] == vc_device ]
        print(bcolors.OKBLUE,f'[Info] : Getting link info for {vc_device} from Jukebox',bcolors.ENDC)
        try:
            device_link = jukebox.get_device_link(vc_device)
        except Exception as error:
            print(bcolors.FAIL,f'[Info] : {error}',bcolors.ENDC)
            sys.exit()
        VC_CAR_AE_LIST = list(df_vc['a_lag'].unique())
        BR_TRA_LIST = list(df_vc['z_hostname'].unique())
        #BR_TRA_LIST = ['syd4-br-tra-r1','syd4-br-tra-r2']
        print(bcolors.HEADER,f'[Info] : Creating VAR/CONF/Bundles for {vc_device}',bcolors.ENDC)
        VC_CAR_INTF_DICT = {}
        VC_CAR_INTF_DICT['interfaces'] = {}

        NEW_LAGS = ','.join(VC_CAR_AE_LIST)
        print(bcolors.OKBLUE,f'[Info] : Creating mapping between {vc_device} and {BR_TRA_LIST}',bcolors.ENDC)

        #get main dict for mapping interfaces
        for indx,series in df_vc.iterrows():
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']] = {}
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['a_lag'] = series['a_lag']
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['z_hostname'] = series['z_hostname']
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['z_interface'] = series['z_interface']
            VC_CAR_INTF_DICT['interfaces'][series['a_interface']]['z_lag'] = series['z_lag']

        # Maps lag to ae --> {'LAG1':{'ae24': [],'LAG2': {'ae25':[]}}
        VC_CAR_LAG_NUM = ['LAG_'+str(count) for count in range(1,len(VC_CAR_AE_LIST)+1)]
        VC_CAR_LAG_DICT = {}
        for lag_num,ae_num in dict(zip(VC_CAR_LAG_NUM,VC_CAR_AE_LIST)).items():
            VC_CAR_LAG_DICT[lag_num] = {}
            VC_CAR_LAG_DICT[lag_num][ae_num] = []
        
        #Appends interfaces to VC_CAR_LAG_DICT 
        for device,intf in VC_CAR_INTF_DICT.items():
            for interface,params in intf.items():
                for lag_num,ae_num in VC_CAR_LAG_DICT.items():
                    for ae,intfs in ae_num.items():
                        if ae == params['a_lag']:
                            intfs.append(interface)
        
        #LAG1,LAG2 interfaces dict --> {'LAG_1_INTERFACES': {'ae24': ['xe-1/1/1','xe-2/2/2']}}
        VC_CAR_LAG_INT_DICT = {}
        VC_CAR_LAG_INT_DICT = {k+'_INTERFACES' : v for k,v in VC_CAR_LAG_DICT.items()}

        #LLDP INFO FOR VAR FILE
        LLDP_INFO = []
        for indx,series in df_vc.iterrows():
            #xe-5/3/1:sfo5-br-tra-r7_et-0/0/68:2
            LLDP_INFO.append(series['a_interface']+':'+series['z_hostname']+'_'+series['z_interface'])
        LLDP_INFO = ','.join(LLDP_INFO)

        #BR_TRA PEER {'PEER_1': 'sfo5-bt-tra-r7','PEER_2':'sfo5-br-tra-r8'} 
        BR_PEER_LIST = ['PEER_'+str(i) for i in range(1,len(BR_TRA_LIST)+1)]
        BR_PEER_DICT = dict(zip(BR_PEER_LIST,BR_TRA_LIST))
        BR_PEER_DICT = {}
        for peer,br_device in dict(zip(BR_PEER_LIST,BR_TRA_LIST)).items():
            BR_PEER_DICT[peer] = {}
            BR_PEER_DICT[peer][br_device] = []

        #BR_TRA PEER INTF DICT {'PEER_1_INTERFACES': 'sfo5-bt-tra-r7','PEER_2_INTERFACES' :'sfo5-br-tra-r8'}
        BR_PEER_INT_DICT = {peer+'_INTERFACES' : br_device for peer,br_device in BR_PEER_DICT.items()}


        #PEER INT INFO - {'PEER_1_LAG': {'sfo5-br-tra-r1': ['xe-0/0/0','xe-1/1/1']}}
        AE_MAPPING = {}
        BR_PEER_INT_LIST = ['PEER_'+str(i)+'_INTERFACES' for i in range(1,len(BR_TRA_LIST)+1)]
        BR_PEER_INT_DICT = {}
        for peer,br_device in dict(zip(BR_PEER_INT_LIST,BR_TRA_LIST)).items():
            BR_PEER_INT_DICT[peer] = {}
            BR_PEER_INT_DICT[peer][br_device] = []       

        for br_device in BR_TRA_LIST:
            df_br = df_vc[df_vc['z_hostname'] == br_device]
            for indx,series in df_br.iterrows():
                if br_device == series['z_hostname']:
                    AE_MAPPING[series['a_lag']] = series['z_lag']
            for peer_int,br_device in BR_PEER_INT_DICT.items():
                for device,rem_intf in br_device.items():
                    for indx,series in df_br.iterrows():
                        if device == series['z_hostname']:
                            rem_intf.append(series['z_interface'])

        # PEER LAG INFO --> {'PEER_1_LAG': 'ae104', 'PEER_2_LAG': 'ae104'}
        BR_PEER_LAG_LIST = ['PEER_'+str(count)+'_LAG' for count in range(1,len(AE_MAPPING)+1)]
        BR_PEER_LAG_DICT = {}
        for k,v in AE_MAPPING.items():
            for peer in BR_PEER_LAG_LIST:
                BR_PEER_LAG_DICT[peer] = v
                
        #P2P IP's
        p2p_dict = {}
        p2p_dict[vc_device] = {}
        p2p_dict[vc_device]['ipv4'] = []
        p2p_dict[vc_device]['ipv6'] = []
        
        p2p_ip = {}
        p2p_ip[vc_device] = {}
        p2p_ip[vc_device]['ipv4'] = []
        p2p_ip[vc_device]['ipv6'] = []

        for br_device in BR_TRA_LIST:
            for data in device_link:
                if data[0] == br_device:
                    p2p_dict[vc_device]['ipv4'].append(data[1]['link_cidr'])
                    p2p_dict[vc_device]['ipv4'].append(data[1]['csc_link_cidr'])
                    p2p_dict[vc_device]['ipv6'].append(data[1]['inet6_link_cidr'])
                            
        for br_device in BR_TRA_LIST:
            for data in device_link:
                if data[0] == br_device:
                    p2p_ip[vc_device]['ipv4'].append(data[1]['link_cidr'].split('/31')[0])
                    p2p_ip[vc_device]['ipv4'].append(data[1]['csc_link_cidr'].split('/31')[0])
                    p2p_ip[vc_device]['ipv6'].append(data[1]['inet6_link_cidr'].split('/127')[0])

        print(bcolors.OKGREEN,f'[Info] : Successfully mapped {vc_device} to {BR_TRA_LIST}',bcolors.ENDC)
        #Create VAR FILE
        with open(f'{path}/{vc_device}.var','w') as var_file:
            var_file.write(f'LOCAL_COR={br_cor}\n')
            var_file.write(f'ADD_LINKS_TO_NEW_LAG=True\n')
            var_file.write(f'IGNORE_ALARMS=,\n')
            var_file.write(f'NEW_LAGS ={NEW_LAGS}\n')
            var_file.write(f'INF_LIGHT_THRESHOLD_HIGH=1\n')
            var_file.write(f'INF_LIGHT_THRESHOLD_LOW=-10\n')
            for lag_num,ae_num in VC_CAR_LAG_DICT.items():
        	    for ae,intfs in ae_num.items():
        	        var_file.write(f'{lag_num}={ae}\n')
            for lag_intf,ae_num in VC_CAR_LAG_INT_DICT.items():
        	    for ae,intfs in ae_num.items():
        	        intfs = ','.join(intfs)
        	        var_file.write(f'{lag_intf}={intfs}\n')
            var_file.write(f'LLDP_NEIGHBORS_INFO={LLDP_INFO}\n')
            for peer,br_device in BR_PEER_DICT.items():
        	    for device,intfs in br_device.items():
        	        var_file.write(f'{peer}={device}\n')
            for peer_intf,br_device in BR_PEER_INT_DICT.items():
        	    for device,rem_inf in br_device.items():
        	        rem_inf = ','.join(rem_inf)
        	        var_file.write(f'{peer_intf}={rem_inf}\n')
            for peer_lag,lag_num in BR_PEER_LAG_DICT.items():
        	    var_file.write(f'{peer_lag}={lag_num}\n')
            for k,v in p2p_dict.items():
        	    x = ','.join(v['ipv4'])
        	    var_file.write(f'P2P_PREFIXES={x}\n')
            for k,v in p2p_ip.items():
        	    x = ','.join(v['ipv4'])
        	    var_file.write(f'PEER_V4_IPS={x}\n')      
            for k,v in p2p_ip.items():
        	    x = ','.join(v['ipv6'])
        	    var_file.write(f'PEER_V6_IPS={x}\n')
            var_file.write(f'MIN_V4_PREFIX=750\n')
            var_file.write(f'MAX_V4_PREFIX=3400\n')
            var_file.write(f'MIN_V6_PREFIX=750\n')
            var_file.write(f'MAX_V6_PREFIX=3200\n')
            var_file.write(f'ENABLE_V6_BGP_ESTABLISHED_CHECK=true\n')
            for k in VC_CAR_LAG_DICT:
                if 'LAG_2' in k:
                    var_file.write(f'ENABLE_LAG_2_CHECKS=true\n')
                if 'LAG_3' in k:
                    var_file.write(f'ENABLE_LAG_3_CHECKS=true\n')
                if 'LAG_4' in k:
                    var_file.write(f'ENABLE_LAG_4_CHECKS=true\n')
            for k in BR_PEER_DICT:
                if 'PEER_2' in k:
                    var_file.write(f'ENABLE_PEER_2_CHECKS=true\n')
                if 'PEER_3' in k:
                    var_file.write(f'ENABLE_PEER_3_CHECKS=true\n')
                if 'PEER_4' in k:
                    var_file.write(f'ENABLE_PEER_4_CHECKS=true\n')
        #END VAR FILE GENERATION
        print(bcolors.OKGREEN,f'[Info] : Sucessfully created VAR file for {vc_device}',bcolors.ENDC)
        #data frame with ae mapping
        df_ae = df_final.drop(['a_interface','z_interface'],axis=1)
        df_ae = df_ae.drop_duplicates()
        #get all v4,csc and ipv6
        v4 = []
        v4_csc = []
        v6 = []

        for info in device_link:
            for indx,series in df_ae.iterrows():
                 if info[0] == series['z_hostname']:
                    v4.append(info[1]['link_cidr'])
                    v4_csc.append(info[1]['csc_link_cidr'])
                    v6.append(info[1]['inet6_link_cidr'])
        df_ae['ipv4'] = v4
        df_ae['ipv4_csc'] = v4_csc
        df_ae['ipv6'] = v6

        #final dict - will be converted to YAML
        VC_CAR_INTF_DICT['ae_interfaces'] = {}
        for indx,series in df_ae.iterrows():
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']] = {}
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['a_hostname'] = series['a_hostname']
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['z_lag'] = series['z_lag']
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['z_hostname'] = series['z_hostname']
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['a_ip'] = (ipaddress.IPv4Address(series['ipv4'].split('/31')[0])+1).compressed
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['a_csc'] = (ipaddress.IPv4Address(series['ipv4_csc'].split('/31')[0])+1).compressed
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['a_ipv6'] = (ipaddress.IPv6Address(series['ipv6'].split('/127')[0])+1).compressed
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['z_ip'] = ipaddress.IPv4Address(series['ipv4'].split('/31')[0]).compressed 
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['z_csc'] = ipaddress.IPv4Address(series['ipv4_csc'].split('/31')[0]).compressed
            VC_CAR_INTF_DICT['ae_interfaces'][series['a_lag']]['z_ipv6'] = ipaddress.IPv6Address(series['ipv6'].split('/127')[0]).compressed

        print(bcolors.OKBLUE,f'[Info] : Creating yaml file for {vc_device}',bcolors.ENDC)
        #create yaml file
        try:
            with open(f'{path}/{vc_device}.yaml','w') as outfile:
                outfile.write(yaml.dump(VC_CAR_INTF_DICT,default_flow_style=False ))
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()

        #load yaml file
        try:
            yaml_file = yaml.safe_load(open(f'{path}/{vc_device}.yaml'))
        except FileNotFoundError as error:
            print(bcolors.FAIL,f'[Error] : Could not load yaml file',bcolors.ENDC)
            sys.exit()

        print(bcolors.OKGREEN,f'[Info] : Successfully created yaml file for {vc_device}',bcolors.ENDC)

        print(bcolors.OKBLUE,f'[Info] : Creating conf file for {vc_device}',bcolors.ENDC)
        
        #template for creating config
        j2_template = Template(
        '''
interfaces {
{% for intf,params in interfaces.items() %}
    replace: {{intf}} {
        description "{{params.z_hostname}} {{params.z_interface}} via {{params.a_lag}}";
        gigether-options {
            802.3ad {{params.a_lag}};
        }
    }
{% endfor %}
{% for intf,ae_info in ae_interfaces.items() %}
    replace: {{intf}} {
        description "{{ae_info.a_hostname}} --> {{ae_info.z_hostname}}";
        flexible-vlan-tagging;
        mtu 9192;
        unit 10 {
            description "{{ae_info.a_hostname}} --> {{ae_info.z_hostname}} INTERNET";
            vlan-id 10;
            family inet {
                mtu 1500;
                address {{ae_info.a_ip}}/31;
                }
            family inet6 {
                mtu 1500;
                address {{ae_info.a_ipv6}}/127;
                }
            }
        unit 11 {
            description "{{ae_info.a_hostname}} --> {{ae_info.z_hostname}} CSC";
            vlan-id 10;
            family inet {
                mtu 1500;
                address {{ae_info.a_csc}}/31;
            }
            family mpls;
        }
    }
{% endfor %}
}
protocols {
    mpls {
        no-propagate-ttl;
        ipv6-tunneling;
        {% for intf,params in ae_interfaces.items() -%}
        interface {{intf}}.11
        {% endfor %}   
    }
    bgp {
        path-selection external-router-id;
        group EBGP-CSC {
            advertise-inactive;
            type external;
            import EBGP-CSC-IN;
            family inet {
                labeled-unicast {
                    loops 2;
                    resolve-vpn;
                }
            }
            export EBGP-CSC-OUT;
            peer-as 16509;
            multipath multiple-as;
            {% for lag,params in ae_interfaces.items() -%}
            neighbor {{params.z_csc}} {
                description "{{ params.z_hostname }}";
                local-address {{ params.a_csc}};
            }
            {% endfor %}
        
        }
        group EBGP-PEERING {
            type external;
            advertise-inactive;
            import BR-IN;
            family inet {
                unicast;
            }
            export [ BGP-REDIST V4-STD-DENY-OUT BR-OUT BR-COMMUNITIES-IAD-OUT ACCEPT-ALL ];
            remove-private;
            peer-as 16509;
            multipath;
            {% for lag,params in ae_interfaces.items() -%}
            neighbor {{ params.z_ip }} {
                description "{{ params.z_hostname }}";
                local-address {{ params.a_ip }};
            }
            {% endfor %}
        
        }
        group IPV6-EBGP-PEERING-BR {
            type external;
            advertise-inactive;
            import IPV6-EBGP-IMPORT-BORDER;
            family inet6 {
                unicast;
            }
            export [ IPV6-BGP-REDIST-BR V6-STD-DENY-OUT IPV6-BR-OUT ];
            remove-private;
            peer-as 16509;
            multipath;
            {% for lag,params in ae_interfaces.items() -%}
            neighbor {{ params.z_ipv6 }} {
                description "{{ params.z_hostname }}";
                local-address {{ params.a_ipv6 }};
            }
            {% endfor %}
        
        }
    }
}
        '''        
        )
        #create config
        try:
            with open(f'{path}/{vc_device}.conf','w') as device_config:
                print(j2_template.render(yaml_file),file=device_config)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
            sys.exit()
        
        print(bcolors.OKGREEN,f'[Info] : Successfully created Conf file for {vc_device}',bcolors.ENDC)
        bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {vc_device} --local-files {vc_device}.conf --policy add_links_to_lag_between_vc-car_and_br-tra.yaml --policy-args-file {vc_device}.var  --approvers l1-approver'
        bundle_commands.append(bundle_command)
        print(bcolors.OKBLUE,f'[Info] : Creating Alfred bundle for {vc_device}',bcolors.ENDC)
        try:
            command_output = subprocess.check_output(bundle_command, shell=True)
        except Exception as error:
            print(bcolors.FAIL,f'[Error] : {error} exiting',bcolors.ENDC)
            sys.exit()
            
        decoded_output = command_output.decode('utf-8').splitlines()
        bundle = decoded_output[-2]
        bundle = bundle.split('https:')[1]
        bundle_dict[vc_device] = 'https:'+bundle
    
    for device,bundle in bundle_dict.items():
        print(bcolors.OKGREEN,f'[Info] : Bundles successfully created',bcolors.ENDC)
        print(bcolors.OKGREEN,f'[Info] : {device} - {bundle}',bcolors.ENDC)
    print(bcolors.OKGREEN,f'[Info] : All VAR/Conf files saved to {path}',bcolors.ENDC)
    
    return bundle_dict,bundle_commands,vc_site_code,vc_car_list,vc_device_regex,br_device_regex

def car_tra_mcm_new_lag(df,vc_car_list,br_tra_list):
    """
    This function creates MCM for CAR-TRA Scaling for new lag

    Args:
        args (args): site code,vc device list, vc device regex, br device regex, gb cr
    """    
    mcm_data = car_tra_bundle_new_lag(df,vc_car_list,br_tra_list)
    bundle_dict = mcm_data[0]
    bundle_commands = mcm_data[1]
    site_code = mcm_data[2]
    device_list = mcm_data[3]
    vc_device_regex = mcm_data[4]
    br_device_regex = mcm_data[5]
    gb_cr = 'CR-1234'
    print(bcolors.OKBLUE,f'[Info] : Creating MCM',bcolors.ENDC)
    # function from mcm.py -  mcm_create = mcm_creation("mcm_title_overview_link_new_lag",'sfo20',['sfo20-vc-car-r1','sfo20-vc-car-r2'],vc_device_regex,br_device_regex)
    try:
        mcm_create = mcm.mcm_creation("mcm_title_overview_link_new_lag",site_code,device_list,vc_device_regex,br_device_regex)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
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
    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)
    for k,v in bundle_dict.items():
        mcm_bundles.append(f'{k} : {v}')
    
    #MCM-steps
    print(bcolors.OKBLUE,f'[Info] : Adding MCM steps',bcolors.ENDC)
    try:
        for command in bundle_commands:
            device_name = command.split('--devices')[1].split('--local-files')[0].strip()
            bundle_id = bundle_dict[device_name].split('/')[-1]
            step = {'title':f'Alfred Bundle Deployment for {device_name}','time':60,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id}', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'}
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
            
def main():
    start_time = perf_counter()
    args = parse_args()
    try:
        info = read_cutsheet_car_tra(args.cutsheet_mcm)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    df_final = info[0]
    vc_car_list = info[1]
    br_tra_list = info[2]
    df_sample  = df_final.sample(1)
    sample_a_device = list(df_sample['a_hostname'].unique())
    sample_z_device = list(df_sample['z_hostname'].unique())
    
    for device in sample_a_device:
        device_type_a = re.search(r"(vc|br)-([a-z][a-z][a-z])", device).group()

    for device in sample_z_device:
        device_type_z = re.search(r"(vc|br)-([a-z][a-z][a-z])", device).group()
    scaling_type = device_type_a+'_'+device_type_z
    
    if scaling_type == 'vc-car_br-tra':
        if args.existing_lag:
            if args.bundle_only:
                car_tra_bundle_existing_lag(df_final,vc_car_list,br_tra_list)
            else:
                car_tra_mcm_existing_lag(df_final,vc_car_list,br_tra_list)
        elif args.new_lag:
            if args.bundle_only:
                car_tra_bundle_new_lag(df_final,vc_car_list,br_tra_list)
            else:
                car_tra_mcm_new_lag(df_final,vc_car_list,br_tra_list)                
    else:
        print(bcolors.FAIL,f'[Error] : Could not find the scaling type - Exiting',bcolors.ENDC)
        sys.exit()
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
