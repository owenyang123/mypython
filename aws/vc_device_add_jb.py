#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import (jukebox,mcm)
from dxd_tools_dev.datastore import ddb
import pandas as pd
from time import perf_counter
import xlwt
import xlrd
import subprocess
import argparse
import string
import random
import sys
import time
import datetime
import re
from random import getrandbits
from ipaddress import IPv4Network, IPv4Address

'''
Author : anudeept@

Script Usage:
usage: vc_device_add_jb.py [-h] -d  -r  -c  [-v4] [-a] [-e]

Script to add new VC device to JukeBox based on cutsheet provided

optional arguments:
  -h, --help            show this help message and exit
  -d , --device         VC DEVICE TO BE ADDED TO JUKEBOX (ex: bjs20-vc-bar-r1)
  -r , --region         REGION (EX: pdx)
  -c , --cutsheet_mcm   CUTSHEET MCM (EX: MCM-1234)
  -v4 , --v4            IPV4 LOOPBACK (ex:1.1.1.1)
  -a, --device_add      ADD NEW DEVICE
  -e, --device_edit     EDIT DEVICE
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
    parser = argparse.ArgumentParser(description="Script to add new VC device to JukeBox based on cutsheet provided")
    parser = argparse.ArgumentParser(description="Script to add new VC device to JukeBox based on cutsheet provided")
    parser.add_argument('-d','--device', type=str, metavar = '', required= True, help = 'VC DEVICE TO BE ADDED TO JUKEBOX (ex: bjs20-vc-bar-r1)')
    parser.add_argument('-r','--region', type=str, metavar = '', required= True, help = 'REGION (EX: pdx)')
    parser.add_argument('-c','--cutsheet_mcm',type=str, metavar = '', required = True, help = 'CUTSHEET MCM (EX: MCM-1234)')
    parser.add_argument('-v4','--v4', type=str, metavar = '', required = False, help = 'IPV4 LOOPBACK (ex:1.1.1.1)')
    parser.add_argument("-a","--device_add",action="store_true",help="ADD NEW DEVICE")
    parser.add_argument("-e","--device_edit",action="store_true",help="EDIT DEVICE")
    return parser.parse_args()

def date_time():
    date_time = datetime.datetime.today()
    return date_time

def random_ip():
    """This function is to generate a random ip address from subnet 10.100.0.0/24 used later in
    the script

    Returns:
        addr_str [string]: Random ip address
    """    
    for i in range(1,20):
        num = random.randint(1,60)
        subnet = IPv4Network(f"10.100.{num}.0/24")
    #bits = 8 in this case
    bits = getrandbits(subnet.max_prefixlen - subnet.prefixlen)
    addr = IPv4Address(subnet.network_address + bits)
    addr_str = str(addr)
    return addr_str

def random_subnet():
    """This function is to generate a random /31 fromsubnet 10.0.{1-50}.0/24 used later in the script

    Returns:
        subnet[string]: Random /31 from 10.0.{1-50}.0/24 
    """     
    for i in range(1,10):
        num = random.randint(1,50)
        subnet = IPv4Network(f"10.10.{num}.0/24")
    #bits = 8 in this case
    bits = getrandbits(subnet.max_prefixlen - subnet.prefixlen)
    addr = IPv4Address(subnet.network_address + bits)
    addr_str = str(addr)
    first_oct = addr_str.split('.')[0]
    second_oct = addr_str.split('.')[1]
    third_oct = addr_str.split('.')[2]
    fourth_oct = addr_str.split('.')[3]
    if int(fourth_oct) % 2 == 0:
        subnet = first_oct+'.'+second_oct+'.'+third_oct+'.'+fourth_oct+'/31'
    else:
        subnet = first_oct+'.'+second_oct+'.'+third_oct+'.'+str(int(fourth_oct)-1)+'/31'
    return subnet

def panda_data_frame(cutsheet_mcm,hostname):
    """This function downloads the latest cutsheet from MCM and returns a pandas data frame 
    and list of devices from the cutsheet

    Args:
        cutsheet_mcm ([string]): Cutsheet MCM ex: MCM-1234
        hostname ([string]): Device Name ex: 'sfo20-vc-car-r1'

    Returns:
        df_final ([pandas data frame])
        cutsheet_a_devices ([list of a side devices])
        cutsheet_z_devices ([list of z side devices])
    """
        
    date_time = datetime.datetime.today()
    print(bcolors.HEADER,f'{date_time} [Info] : Downloading cutsheet from MCM',bcolors.ENDC)
    #download cutsheet from mcm.py module
    try:
        cutsheet = mcm.download_latest_cutsheet(cutsheet_mcm)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()

    try:
        df = pd.read_excel(cutsheet,engine='xlrd',sheet_name=None)
    except FileNotFoundError:
        print(bcolors.FAIL,f'{date_time} [Error] : Could not find {cutsheet}')
        sys.exit()
    
    # new empty data frame
    df_new = pd.DataFrame()
    
    # verify data frame is valid
    if len(df) != 0:
        for info in df.items():
            df_new = df_new.append(info[1])
    else:
        print(bcolors.FAIL,f'{date_time} [Error] : Excel sheet is not in the right format, please verify',bcolors.ENDC)
        sys.exit()
    
    #drop empty lines in data frame
    df_new = df_new.dropna(axis=0,how='all')
    df_new = df_new.dropna(axis=1,how='all')

    #create a dataframe specific to the user input
    try:
        df_a = df_new[df_new['a_hostname'] == hostname]
        df_z = df_new[df_new['z_hostname'] == hostname]
    except:
        print(bcolors.FAIL,f'{date_time} [Error] : Could not find {hostname} in cutsheet, please check the argument passed',bcolors.ENDC)
        sys.exit()
    
    df_z = df_z.rename(columns={'a_hostname': 'z_hostname', 'a_interface': 'z_interface','z_hostname': 'a_hostname','z_interface': 'a_interface'})
    df_z = df_z[['a_hostname','a_interface','z_hostname','z_interface']]
    
    df_final = df_a.append(df_z,ignore_index=True)

    try:
        df_final = df_final[['a_hostname','a_interface','z_hostname','z_interface']]
    except Exception as e:
        print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
        print(bcolors.FAIL,f'{date_time} [Error] : Please make sure cutsheet has a_hostname,a_interface,z_hostname,z_interface columns',bcolors.ENDC)
        sys.exit()
    
    print(bcolors.OKBLUE,f'{date_time} [Info] : Getting list of devices from cutsheet',bcolors.ENDC)
    # Create list of devices in the cutsheet
    try:
        cutsheet_a_devices = list(df_final['a_hostname'].unique())
        cutsheet_a_devices = [str(device) for device in cutsheet_a_devices]
    except KeyError:
        print(bcolors.FAIL,f'{date_time} [Error] : Could not find a_hostname column in cutsheet, please check cutsheet',bcolors.ENDC)
        sys.exit()

    try:
        cutsheet_z_devices = list(df_final['z_hostname'].unique())
        cutsheet_z_devices = [str(device) for device in cutsheet_z_devices]
    except KeyError:
        print(bcolors.FAIL,f'{date_time} [Error] : Could not find a_hostname column in cutsheet, please check cutsheet',bcolors.ENDC)
        sys.exit()
    cutsheet_a_devices = [device for device in cutsheet_a_devices if not "nan" in device and device]
    cutsheet_z_devices = [device for device in cutsheet_z_devices if not "nan" in device and device]
    print(bcolors.OKGREEN,f'{date_time} [Info] : From cutsheet {hostname} connects to {cutsheet_z_devices}',bcolors.ENDC)
    #function returns pandas data frame, list of a side and z side devices
    return df_final,cutsheet_a_devices,cutsheet_z_devices

def create_device(cutsheet_mcm,device,region,v4_ip=None):
    
    """This function is to create a coral device in JukeBox format.This function reads the cutsheet
    and returns coral_device, which is used in the next function to push the device

    Args:
        cutsheet_mcm [string] : Cutsheet MCM
        device [string] : Device name passed as argument
        region [string] : Region
        v4_ip [string] : Optional 
        
    Returns:
        device_new : device in coral format for Jukebox
    """

    if 'vc-bar' in device:
        model = 'QFX10002-72Q'
    elif 'vc-edg' in device:
        model = 'MX480'
    elif 'vc-cir' in device:
        model = 'MX240'
    elif 'vc-xlc' in device:
        model = 'QFX5100-96S-8Q'
    elif 'vc-ecr' in device:
        model = 'MX10003'
    
    date_time = datetime.datetime.today()

    region_list = ['arn','bah','bjs','bom','cdg','cmh','corp','dub','fra','gru','hkg','iad','icn','kix','lhr','mxp','nrt','pdx','pek','sfo','sin','syd','yul','zhy']

    vendor = 'Juniper'
    az = device.split('-')[0]
    
    print(bcolors.OKBLUE,f'{date_time} [Info] : Validating user passed argument for region',bcolors.ENDC)

    if region in region_list:
        region = region
    else:
        print(bcolors.FAIL,f'{date_time} [Info] : {region} in not valid, please check the argument',bcolors.ENDC)
        sys.exit()

    v6_address = ''
    v4_address = random_ip()

    chars = string.ascii_uppercase 
    random_serial = ''.join(random.choice(chars) for _ in range(5))

    
    df_data = panda_data_frame(cutsheet_mcm,device)

    # Create list of devices in the cutsheet
    a_devices = df_data[1]

    print(bcolors.OKBLUE,f'{date_time} [Info] : Verifying if {device} is in Cutsheet',bcolors.ENDC)

    #verify if the argument provided for device is in the cutsheet
    if device in a_devices:
        print(bcolors.OKGREEN, f'{date_time} [Info] : {device} is in cutsheet',bcolors.ENDC)
    else:
        print(bcolors.FAIL,f'{date_time} [Error] : {device} is not cutsheet, please check the argument passed',bcolors.ENDC)
        sys.exit()

    print(bcolors.OKBLUE,f'{date_time} [Info] : Verifying, if {device} does not exist in JukeBox, this might take few minutes',bcolors.ENDC)
    
    try:
        devices_in_region = jukebox.get_all_devices_in_jukebox_region(region)
    except:
        print(bcolors.FAIL,f'{date_time} [Error] : Unexpected result, exiting',bcolors.ENDC)

    #verify args.device not in jb
    if device in devices_in_region:
        print(bcolors.FAIL,f'{date_time} [Error] : {device} is already in Jukebox, exiting',bcolors.ENDC)
        sys.exit()
    else:
        print(bcolors.OKGREEN,f'{date_time} [Info] : {device} does not exist in JukeBox',bcolors.ENDC)    

    print(bcolors.OKBLUE,f'{date_time} [Info] : Creating {device} for Jukebox')

    # device_new = jukebox.create_coral_device(args.device,"Juniper","QFX10002-72Q","ABCD","1.1.1.1","","bjs")
    if v4_ip:
        try:
            device_new = jukebox.create_coral_device(device,vendor,model,random_serial,v4_ip,v6_address,region)
        except Exception as e:
            print(bcolors.FAIL,f"{date_time} [Error] : {device} could not be created, exiting",bcolors.ENDC)
            print(bcolors.FAIL,f"{date_time} [Error] : {e}",bcolors.ENDC)
            sys.exit()
    else:
        try:
            device_new = jukebox.create_coral_device(device,vendor,model,random_serial,v4_address,v6_address,region)
        except Exception as e:
            print(bcolors.FAIL,f"{date_time} [Error] : {device} could not be created, exiting",bcolors.ENDC)
            print(bcolors.FAIL,f"{date_time} [Error] : {e}",bcolors.ENDC)
            sys.exit()

    print(bcolors.OKGREEN,f'{date_time} [Info] : {device} created for Jukebox',bcolors.ENDC)

    #Add new device to Dynamo DDB 
    print(bcolors.OKBLUE,f'{date_time} [Info] : Adding {device} to dynamo DB',bcolors.ENDC)
    try:
        ddb.add_device_to_dx_region_table(region,device)
    except Exception as e:
        print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
        sys.exit()
    print(bcolors.OKGREEN,f'{date_time} [Info] : Added {device} to dynamo DB',bcolors.ENDC)
    return device_new

def add_new_device_jb(args):
    """This function is add the device to Jukebox

    Args:
        args : arguments passed by user
    """
    date_time = datetime.datetime.today()
    if args.v4:
        #create_device(cutsheet_mcm,device,region,v4_ip=None)
        device_new = create_device(args.cutsheet_mcm,args.device,args.region,args.v4)
    else:
        device_new = create_device(args.cutsheet_mcm,args.device,args.region)
    
    az = args.device.split('-')[0]
    try:
        jukebox.add_new_device_to_jb(device_new,[],[],az)
    except Exception as error:
        print(bcolors.FAIL,f'{date_time} [Error] : {error}',bcolors.ENDC)
        sys.exit()
        
    print(bcolors.OKBLUE,f"{date_time} [Info] : {args.device} uploaded to JukeBox, please get approvals - https://jukebox-web.corp.amazon.com/#/pendingEdits ",bcolors.ENDC)

def edit_cabling_cidr(cutsheet_mcm,hostname,region):
    """This function reads cutsheet and creates cabling/cidr info

    Args:
        cutsheet_mcm [string] : Cutsheet MCM
        device [string] : device name
        region [string] : region
    
    """
    date_time = datetime.datetime.today()

    df_data = panda_data_frame(cutsheet_mcm,hostname)
    az = hostname.split('-')[0]

    region_list = ['arn','bah','bjs','bom','cdg','cmh','corp','dub','fra','gru','hkg','iad','icn','kix','lhr','mxp','nrt','pdx','pek','sfo','sin','syd','yul','zhy']

    print(bcolors.OKBLUE,f'{date_time} [Info] : Validating user passed argument for region',bcolors.ENDC)

    if region in region_list:
        region = region
    else:
        print(bcolors.FAIL,f'{date_time} [Info] : {region} in not valid, please check the argument',bcolors.ENDC)
        sys.exit()

    # Create list of a_devices in the cutsheet
    a_devices = df_data[1]

    print(bcolors.OKBLUE,f'{date_time} [Info] : Verifying {hostname} is in cutsheet',bcolors.ENDC)

    #verify if the argument provided for device is in the cutsheet
    if hostname in a_devices:
        print(bcolors.OKGREEN, f'{date_time} [Info] : Found {hostname} in cutsheet',bcolors.ENDC)
    else:
        print(bcolors.FAIL,f'{date_time} [Error] : {hostname} is not in cutsheet, please check the argument passed',bcolors.ENDC)
        sys.exit()    

    print(bcolors.OKBLUE,f'{date_time} [Info] : Verifying, if {hostname} already exists in JukeBox, this might take few minutes',bcolors.ENDC)
    
    try:
        devices_in_region = jukebox.get_all_devices_in_jukebox_region(region)
    except:
        print(bcolors.FAIL,f'{date_time} [Error] : Unexpected result, exiting',bcolors.ENDC)
        sys.exit()

    #verify args.device not in jb
    if hostname not in devices_in_region:
        print(bcolors.FAIL,f'{date_time} [Error] : {hostname} is not in Jukebox, exiting',bcolors.ENDC)
        sys.exit()
    else:
       print(bcolors.OKGREEN,f'{date_time} [Info] : Found {hostname} in JukeBox',bcolors.ENDC)

    print(bcolors.OKBLUE,f'{date_time} [Info] : Reading cabling info for {hostname} from cutsheet',bcolors.ENDC)

    #Create the Pandas data frame
    df_cabling_final = df_data[0]
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'em0']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'fxp0']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'mgmt']
    df_cabling_final = df_cabling_final[~df_cabling_final['z_hostname'].str.contains("vc-ecr")]
    df_cabling_final = df_cabling_final[df_cabling_final['a_hostname'] != df_cabling_final['z_hostname']]
    df_cabling_final = df_cabling_final.drop_duplicates()

    print(bcolors.OKBLUE,f'{date_time} [Info] : Getting cabling info for {hostname} from JukeBox',bcolors.ENDC)

    try:
        device_cabling = jukebox.get_cabling_coral(hostname)
    except Exception as error:
        print(bcolors.FAIL,f'{date_time} [Error] : {error}',bcolors.ENDC)
        sys.exit()
        
    #this list will keep of track of existing links in JB and excludes them when appending
    links_in_jb = []
    
    #get device cabling detail to match the interfaces
    device_cabling_detail = jukebox.get_device_cabling_detail(hostname)
    
    for link in device_cabling_detail:
        links_in_jb.append(link[1])
    
    #Append cabling only if links are not in JB
    for indx,series in df_cabling_final.iterrows():
        if series['a_interface'] not in links_in_jb:
            try:
                new_cabling = jukebox.append_device_cabling(hostname.strip(),series['a_interface'].strip(),series['z_hostname'].strip(),series['z_interface'].strip(),device_cabling)
            except Exception as error:
                print(bcolors.FAIL,f'{date_time} [Error] : {error}',bcolors.ENDC)
                sys.exit()
            
    print(bcolors.OKGREEN,f'{date_time} [Info] : Appended cabling info from cutsheet',bcolors.ENDC)

    print(bcolors.HEADER,f'{date_time} [Info] : Reading CIDR spreadsheet to get P2P IP',bcolors.ENDC)

    # code for appending CIDR Info    
    #read cidr spreadsheet
    try:
        df_ip = pd.read_excel('/apollo/env/DXDeploymentTools/cutsheet_templates/cidr_hambone.xlsx',sheet_name=None)
    except FileNotFoundError:
        print(bcolors.FAIL,f'{date_time} [Error] : Could not find cidr_spreasheet, please provide full path to the cidr spreadsheet',bcolors.ENDC)
        sys.exit()    
    
    #empty cidr data frame
    df_cidr = pd.DataFrame()

    for info in df_ip.items():
        df_cidr = df_cidr.append(info[1])
        
    df_cidr['a_hostname'] = df_cidr['a_hostname'].str.lower()
    df_cidr['z_hostname'] = df_cidr['z_hostname'].str.lower()
    
    #Look for hostname in cidr sheet
    #search_name = host.split('-')[-2]+'-'+host.split('-')[-1]
    dev_reg = re.search(r'(edg|bar|cir|xlc|svc).*[0-9]$',hostname)

    if dev_reg != None:
        try:
            df_ip_a = df_cidr[df_cidr['a_hostname'] == dev_reg.group()]
            df_ip_z = df_cidr[df_cidr['z_hostname'] == dev_reg.group ()]
        except Exception as e:
            print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
            sys.exit()

    df_ip_z = df_ip_z.rename(columns={'a_hostname': 'z_hostname','z_hostname': 'a_hostname'})
    df_ip_z = df_ip_z[['a_hostname','z_hostname','p2p_ip']]

    #final data frame with cidr info for the host
    df_link_final = df_ip_a.append(df_ip_z,ignore_index=True)
    
    #read cabling cutsheet
    z_devices = df_data[2]
    search_z_devices = []
    #from z_devices appends last two items of split
    for device in z_devices:
        search_z_devices.append(device.split('-')[-2]+'-'+device.split('-')[-1])
        
    #df_link_final = df_link_final[df_link_final['z_hostname'].isin(search_z_devices)]
    
    #create empty csc_ip column
    df_link_final['csc_ip'] = ''

    for z_device in search_z_devices:
        if 'agg' in z_device or 'svc' in z_device:
            df_link_final = df_link_final.append({'a_hostname' : dev_reg.group(), 'z_hostname' : z_device, 'p2p_ip' : random_subnet(),'csc_ip' : random_subnet()}, ignore_index=True)
            
    df_link_final = df_link_final.sort_values(by='z_hostname')
    
    z_column_names = []
    br_site_code = []
    for z_device in z_devices:
        if 'agg' in z_device:
            br_site_code.append(z_device.split('-br-')[0])
    
    br_site_code = list(set(br_site_code))
        
    for indx,series in df_link_final.iterrows():
        if 'agg' in series['z_hostname']:
            z_column_names.append(''.join(br_site_code)+'-br-'+series['z_hostname'])
        else:
            z_column_names.append(hostname.split('-')[0]+'-vc-'+series['z_hostname'])
            
    df_link_final['z_hostname'] = z_column_names
    
    #final data frame to work with 
    df_final = pd.DataFrame() 
    for indx,series in df_link_final.iterrows():
        if series['z_hostname'] in z_devices:
            df_final = df_final.append(series)
            
    df_final = df_final[['a_hostname','z_hostname','p2p_ip','csc_ip']]
    
    print(bcolors.OKBLUE,f'{date_time} [Info] : Fetching link info for {hostname} from JukeBox',bcolors.ENDC)

    device_links = jukebox.get_cidr_coral(hostname)

    print(bcolors.OKBLUE,f'{date_time} [Info] : Adding links from CIDR sheet to {hostname}',bcolors.ENDC)
    
    #cidr_info(a_hostname,z_hostname,ipv4_cidr,ipv4_csc_cidr,link_type,link_cidr_list = [])
    for indx,series in df_final.iterrows():
        random_sub = random_subnet()
        if 'br-agg' in series['z_hostname']:
            try:
                new_link_info = jukebox.append_device_cidr(hostname,series['z_hostname'].strip(),series['p2p_ip'],series['csc_ip'].strip(),'border',device_links)
            except Exception as e:
                print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
                sys.exit()
        else:
            try:
                new_link_info = jukebox.append_device_cidr(hostname,series['z_hostname'].strip(),series['p2p_ip'].strip(),'','internal',device_links)
            except Exception as e:
                print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
                sys.exit()
    
    for z_device in z_devices:
        if 'vc-svc' in z_device:
            new_link_info = jukebox.append_device_cidr(hostname,z_device.strip(),'10.0.0.2/31','','ec2',device_links)
            
    print(bcolors.OKGREEN,f'{date_time} [Info] : Cabling/link cidr info updated',bcolors.ENDC)

    return new_cabling,new_link_info

def edit_device_jb(args):
    """This function pushes the device information to JukeBox

    Args:
        args : user arguments
    """
    #edit_cabling_cidr(cutsheet_mcm,device,region)
    device_info = edit_cabling_cidr(args.cutsheet_mcm,args.device,args.region)
    device_cabling = device_info[0]
    device_cidr = device_info[1]
    date_time = datetime.datetime.today()
    try:
        jukebox.edit_full_device(args.device,device_cabling,device_cidr)
    except Exception as e:
        print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
        sys.exit()
    print(bcolors.OKBLUE,f"{date_time} [Info] : Added cabling/cidr information to Jukebox from cutsheet for {args.device} - please check https://jukebox-web.corp.amazon.com/#/pendingEdits ",bcolors.ENDC)
  
def main():
    start_time = perf_counter()
    args = parse_args()
    if args.device_add:
        add_new_device_jb(args)
    elif args.device_edit:
        edit_device_jb(args)
    else:
        print(bcolors.FAIL,f'[Error] : User did not specify the right function, should be device_add or device_edit - exiting',bcolors.ENDC)
        sys.exit()
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
