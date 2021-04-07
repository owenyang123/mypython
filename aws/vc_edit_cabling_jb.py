#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import pandas as pd
import xlwt
import sys
from dxd_tools_dev.modules import jukebox
import argparse


'''
Summary: This script is used to update cabling info from cutsheet to JukeBox.                 

Command to execute the script:

/apollo/env/DXDeploymentTools/bin/vc_edit_cabling_jb.py --cutsheet '/home/anudeept/SYD52_BR_AGG_JB.xlsx' --device 'syd52-vc-bar-r1'

usage: vc_edit_cabling_jb.py [-h] -c -d

Script to add new VC device to JukeBox based on cutsheet provided

optional arguments:
  -h, --help          show this help message and exit
  -c , --cutsheet     Full path to the cutsheet (ex:/home/anudeept/BJS20-HAMboneV7.xlsx)
  -d , --device       vc device

Version:# 2.0
Author : anudeept@                                                                          
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
    parser = argparse.ArgumentParser(description="Script to add cabling info to JukeBox from cutsheet")
    parser.add_argument('-d','--device', type=str, metavar = '', required= True, help = 'vc device')
    parser.add_argument('-c','--cutsheet',type=str, metavar = '', required = True, help = 'Full path to the cutsheet (ex: /home/anudeept/BJS20-HAMboneV7.xlsx)')
    return parser.parse_args()   


def cabling_info(args):
    print(bcolors.HEADER,f"Info >> Reading info from Cutsheet",bcolors.ENDC)
    df = pd.read_excel(args.cutsheet,sheet_name=None)
    df_new = pd.DataFrame()
    
    # verify df 
    if len(df) != 0:
        for info in df.items():
            df_new = df_new.append(info[1])
    else:
        print(bcolors.FAIL,f'Error >> Excel sheet is not in the right format, please verify',bcolors.ENDC)
        sys.exit()

    df_new = df_new.dropna(axis=0,how='all')
    df_new = df_new.dropna(axis=1,how='all')
    
    # Get list of a side devices
    try:
        a_devices = list(df_new['a_hostname'].unique())
        a_devices = [str(device) for device in a_devices]
    except KeyError:
        print(bcolors.FAIL,f'Error >> Could not find a_hostname column in cutsheet, please check cutsheet',bcolors.ENDC)
        sys.exit()

    #Check if required column names are in cutsheet
    try:
        df_cabling = df_new[['a_hostname','a_interface','z_hostname','z_interface']]
    except:
        print(bcolors.FAIL,f'Error >> Cutsheet not in right format for script',bcolors.ENDC)
        print(bcolors.FAIL,f'Error >> Please check https://w.amazon.com/bin/view/DXDEPLOY_Automation_Others/Scripts/vc_edit_cabling_jb.py/',bcolors.ENDC)
        sys.exit()
    
    print(bcolors.OKGREEN,f"INFO >> Cutsheet is valid",bcolors.ENDC)

    print(bcolors.OKBLUE,f'INFO >> Verifying if {args.device} is in cutsheet',bcolors.ENDC)

    if args.device not in a_devices:
        print(bcolors.FAIL,f'INFO >> {args.device} is not in cutsheet, please check the argument passed',bcolors.ENDC)
    else:
        print(bcolors.OKGREEN,f'INFO >> Found {args.device} in cutsheet',bcolors.ENDC)
        
    df_cabling = df_cabling.dropna(axis=0,how='all')
    df_cabling = df_cabling.dropna(axis=1,how='all')
    
    final_df = df_cabling[df_cabling['a_hostname'] == args.device]
    final_df = final_df.dropna(axis=0,how='all')
    final_df = final_df.dropna(axis=1,how='all')
    
    print(bcolors.OKBLUE,f"Info >> Creating cabling for {args.device}",bcolors.ENDC)
    
    #get cabling info from JukeBox
    try:
        device_cabling = jukebox.get_device_detail(args.device).data.cabling
    except:
        print(bcolors.FAIL,f"Error >> Could not get cabling info for {args.device}, please check {args.device} exists in Jukebox and try again",bcolors.ENDC)
        sys.exit()
    
    print(bcolors.OKBLUE,f"Info >> Updating cabling info from cutsheet for {args.device}",bcolors.ENDC)
    
    #Create new cabling info, append data from cutsheet
    for indx,series in final_df.iterrows():
        try:
            new_cabling = jukebox.create_new_cable_info(args.device.strip(),series['a_interface'].strip(),series['z_hostname'].strip(),series['z_interface'].strip(),device_cabling)
        except:
            print(bcolors.FAIL,f'Error >> Could not add cabling info from cutsheet, exiting',bcolors.ENDC)
    
    #Update Jukebox
    try:
        jukebox.edit_jukebox_cabling(args.device,new_cabling)
    except:
        print(bcolors.FAIL,f"Error >> Could not push cabling info from cutsheet for {args.device}",bcolors.ENDC)
        sys.exit()
    
    print(bcolors.OKGREEN,f"Info >> Updated JukeBox, please verify edits : https://jukebox-web.corp.amazon.com/#/pendingEdits",bcolors.ENDC)

def main():
    args = parse_args()
    cabling_info(args)

if __name__ == "__main__":
    main()
