#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import jukebox
import pandas as pd
import xlwt
import subprocess
import argparse
import string
import random
import sys
import time
import datetime
import re
import os
from random import getrandbits
from ipaddress import IPv4Network, IPv4Address

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
    parser.add_argument('-d','--device', type=str, metavar = '', required= True, help = 'VC Device to be added to Jukebox (ex: bjs20-vc-bar-r1)')
    parser.add_argument('-c','--cutsheet',type=str, metavar = '', required = True, help = 'Full path to the cutsheet (ex: /home/anudeept/BJS20-HAMboneV7.xlsx)')
    return parser.parse_args()

def panda_data_frame(cutsheet,hostname):

    ''' Thus function reads the cutsheet and 
    converts it into a Pandas data frame, returns the
    data frame and list of devices in the 
    cutsheet'''
    
    date_time = datetime.datetime.today()
    print(bcolors.HEADER,f'{date_time} [Info] : Reading cutsheet',bcolors.ENDC)

    try:
        df = pd.read_excel(cutsheet,sheet_name=None)
    except FileNotFoundError:
        print(bcolors.FAIL,f'{date_time} [Error] : Could not find {cutsheet}, please provide full path to the cutsheet')
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

def csv_gen(args):
    ''' 
    This function is to generate the CSV file for Mobius
    '''
    date_time = datetime.datetime.today()
    #get username for user
    username = os.getlogin()

    df_data = panda_data_frame(args.cutsheet,args.device)

    # Create list of devices in the cutsheet
    a_devices = df_data[1]

    #Generate CSV
    df_cabling_final = df_data[0]
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'em0']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'mgmt']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 're0_mgmt']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 're1_mgmt']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'fxp0']
    df_cabling_final = df_cabling_final[df_cabling_final['a_interface'] != 'fxp1']
    df_cabling_final = df_cabling_final[~df_cabling_final['z_hostname'].str.contains("vc-ecr")]
    df_cabling_final = df_cabling_final[df_cabling_final['a_hostname'] != df_cabling_final['z_hostname']]
    df_cabling_final = df_cabling_final.drop_duplicates()
    print(bcolors.OKBLUE,f'{date_time} [Info] : Creating CSV file for mobius testing',bcolors.ENDC)
    try:
        df_cabling_final.to_csv(f'/home/{username}/{args.device}-mobius.csv',header = False,index = False)
    except Exception as e:
        print(bcolors.FAIL,f'{date_time} [Error] : {e}',bcolors.ENDC)
        sys.exit()
    print(bcolors.OKGREEN,f'{date_time} [Info] : CSV created',bcolors.ENDC)
    print(bcolors.OKGREEN,f'{date_time} [Info] : Full path to CSV file : /home/{username}/{args.device}-mobius.csv ',bcolors.ENDC)

  
def main():
    args = parse_args()
    csv_gen(args)

if __name__ == "__main__":
    main()
