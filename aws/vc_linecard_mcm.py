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

'''
Summary: This script is used to create a Daryl MCM with the VAR files need. 
Once the script is run, user needs to change the time and submit for approval.              

Command to execute the script:

/apollo/env/DXDeploymentTools/bin/vc_linecard_mcm.py --device "sfo5-vc-car-r1" --slots "7" "2"

usage: vc_linecard_mcm.py [-h]  

Script to add new VC device to JukeBox based on cutsheet provided

optional arguments:
  -h, --help        show this help message and exit
  -d , --device     Name of the device
  -s , --slots      List of slots

Version:# 1.0
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

def user_input():
    #Linecard Selection from user
    print(bcolors.OKBLUE,f"Line Card Selection",bcolors.ENDC)
    print(bcolors.OKBLUE,f"Enter 1 for MPC 3D 16x 10GE",bcolors.ENDC)
    print(bcolors.OKBLUE,f"Enter 2 for MPC 4D 32x 10GE",bcolors.ENDC)
    print(bcolors.OKBLUE,f"Enter 3 for MPCE Type 2 3D",bcolors.ENDC)
    print(bcolors.OKBLUE,f"Enter 4 for MPC7E 3D MRATE",bcolors.ENDC)

    while True:
        try:
            linecard_selection = int(input(f" Please choose the linecard you are installing from the above list: "))
        except ValueError:
            print(bcolors.FAIL,f"Error >> User selected input is not a number, exiting - please try again\n",bcolors.ENDC)
            sys.exit()
        if linecard_selection == 1:
            linecard_type = "MPC 3D 16x 10GE"
            break
        elif linecard_selection == 2:
            linecard_type = "MPC 4D 32x 10GE"
            break
        elif linecard_selection == 3:
            linecard_type = "MPCE Type 2 3D"
            break
        elif linecard_selection == 4:
            linecard_type = "MPC7E 3D MRATE"
            break
        else:
            print(bcolors.WARNING,f"INFO >> Wrong selection, please select a number between 1-4",bcolors.ENDC)
    return linecard_type,linecard_selection

def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Script to create MCM for line card installations with Daryl instructions")
    parser.add_argument('-d','--device',type=str, metavar = '', required = True, help = 'Name of the device')
    parser.add_argument('-s','--slots',nargs = '+',metavar='', required = True, help = 'Slots for the device (format : "7" "2"')
    return parser.parse_args()

def slot_check(args):
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

    print(bcolors.BOLD,f"INFO >> Device/FPC slot validation complete, proceeding to create MCM and VAR files",bcolors.ENDC)
    
def linecard_mcm(args):
    print(bcolors.BOLD,f"INFO >> Starting MCM/VAR creation",bcolors.ENDC)
    site_code = args.device.split('-')[0]
    site_info = jukebox.get_site_region_details(site=site_code)
    region = site_info.region.realm.upper()
    
    num_of_lc = len(args.slots)
    user_selection = user_input()
    linecard_type = user_selection[0]
    linecard_selection = user_selection[1]

    # Call mcm module to create an MCM with user arrgs
    mcm_info = mcm.mcm_title_overview_vc_linecard_insert(args.device,linecard_type,args.slots,num_of_lc)
    mcm_overview = mcm_info[1]

    #Create the MCM
    mcm_create = mcm.mcm_creation("mcm_title_overview_vc_linecard_insert",args.device,linecard_type,args.slots,num_of_lc)
    
    #get mcm id
    mcm_id = mcm_create[0]
    
    #get mcm uid
    mcm_uid = mcm_create[1]
    
    print(bcolors.OKGREEN,f"INFO >> Successfully created MCM - https://mcm.amazon.com/cms/{mcm_id}",bcolors.ENDC)
    
    print(bcolors.OKBLUE,f"INFO >>  Creating DARYL VAR file",bcolors.ENDC)
    username = os.getlogin()
    
    print(bcolors.OKBLUE,f"INFO >> Checking if DxVpnCM2014 exists on home directory")
    if os.path.exists(f'/home/{username}/DxVpnCM2014/') == True:
        repo = git.Repo(f'/home/{username}/DxVpnCM2014')
        origin = repo.remote('origin')
        print(bcolors.OKGREEN,f"INFO >> DxVpnCM2014 Package exists on user home directory",bcolors.ENDC)
        print(bcolors.OKBLUE,f"INFO >> Checking {username} exists under DxVpnCM2014/cm directory",bcolors.ENDC)
        if os.path.exists(f'/home/{username}/DxVpnCM2014/cm/{username}') == True:
            print(bcolors.OKGREEN,f"INFO >> {username} exists under DxVpnCM2014/cm directory",bcolors.ENDC)
            print(bcolors.OKBLUE,f"INFO >> Performing  git pull",bcolors.ENDC)
            origin.pull()
        else:
            print(bcolors.WARNING,f"INFO >> {username} does not exists under DxVpnCM2014/cm directory, creating one ",bcolors.ENDC)
            os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}')
            print(bcolors.OKGREEN, f"INFO >> Successfully created user directory under DxVpnCM2014/cm",bcolors.ENDC)
            print(bcolors.OKBLUE,f"INFO >> Performing  git pull",bcolors.ENDC)
            origin.pull()
    else:
        print(bcolors.WARNING,f"INFO >> DxVpn2014 does not exist on users home directory",bcolors.ENDC)
        print(bcolors.OKBLUE,f"INFO >> Cloning DxVpnCM2014 repo to /home/{username}, this will take a few minutes",bcolors.ENDC)
        try:
            git.Repo.clone_from('ssh://git.amazon.com/pkg/DxVpnCM2014',to_path = f'/home/{username}/DxVpnCM2014')
            repo = git.Repo(f'/home/{username}/DxVpnCM2014')
            origin = repo.remote('origin')
        except:
            print(bcolors.FAIL,f"Error >> Could not clone DxVpnCM2014 to /home/{username}, please clone the repo manually, discard {mcm_id} and run the script again, exiting",bcolors.ENDC)
            print(bcolors.FAIL,f"Error >> git clone ssh://git.amazon.com/pkg/DxVpnCM2014",bcolors.ENDC)
            sys.exit()
        if os.path.exists(f'/home/{username}/DxVpnCM2014/cm/{username}') == True:
            print(bcolors.OKGREEN,f"INFO >> {username} exists under DxVpnCM2014/cm directory",bcolors.ENDC)
            print(bcolors.OKBLUE,f"INFO >> Performing  git pull",bcolors.ENDC)
            origin.pull()
        else:
            print(bcolors.OKBLUE,f"INFO {username} does not exists under DxVpnCM2014/cm directory, creating one ",bcolors.ENDC)
            os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}')
            print(bcolors.OKGREEN, f"INFO >> Successfully created user directory under DxVpnCM2014/cm",bcolors.ENDC)
            print(bcolors.OKBLUE,f"INFO >> Performing  git pull",bcolors.ENDC)
            origin.pull()
    
    #create VAR file
    print(bcolors.OKBLUE,f"INFO >> Creating VAR files for Daryl",bcolors.ENDC)
    with open(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}_{args.device}.var','a') as var_file:
        print(f"## set REGION = '{region}'",file = var_file)
        print(f"## set CM = '{mcm_id}'",file = var_file)
        print(f"## set ROUTER = '{args.device}'",file = var_file)
        print(f"## set FPC_SLOTS = {args.slots}",file = var_file)
        print(f"## set CHASSIS_ALARMS_TO_IGNORE = ''", file = var_file)
        print(f"## set SYSTEM_ALARMS_TO_IGNORE = ''\n",file = var_file)
        if linecard_selection == 4:
            print(f"## set FPC_TYPE = '{user_input.linecard_type}'\n",file = var_file)
        print("{% include 'brazil://DxVpnCMTemplates/templates/fpc_install_vc-car.jt' %}", file = var_file)
        var_file.close()
    
    print(bcolors.OKGREEN,f"INFO >> Created VAR file /home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}_{args.device}.var",bcolors.ENDC)
    
    print(bcolors.OKBLUE,f"INFO >> Pushing VAR file to DxVpnCM2014 repo",bcolors.ENDC)
    repo = git.Repo(f'/home/{username}/DxVpnCM2014')
    print(bcolors.OKBLUE,f"INFO >> Adding files to git repo DxVpnCM2014 ",bcolors.ENDC)
    repo.index.add([f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}_{args.device}.var'])
    print(bcolors.OKGREEN,f"INFO >> Git status\n   {repo.git.status()}\n",bcolors.ENDC)
    while True:
        print(bcolors.OKBLUE,f"INFO >> cm/{username}/{mcm_id}_{args.device}.var will be pushed to DxVpnCM2014",bcolors.ENDC)
        user_input_repo = str(input("Do you want to proceed (yes or no): "))
        if user_input_repo == "yes":
            repo.index.commit(f'{mcm_id} files')
            origin = repo.remote('origin')
            origin.push()
            print(bcolors.OKGREEN,f"INFO >> VAR file successfully pushed to DxVpnCM2014 repo",bcolors.ENDC)
            break
        elif user_input_repo == "no":
            print(bcolors.FAIL,f"INFO >> User selected to optout",bcolors.ENDC)
            print(bcolors.FAIL,f"INFO >> Please checkout staged files from DxVpnCM2014 repo",bcolors.ENDC)
            print(bcolors.FAIL,f"INFO >> Please update https://mcm.amazon.com/cms/{mcm_id} manually with Daryl steps and VAR files- exiting",bcolors.ENDC)
            sys.exit()
        else:
            print(bcolors.WARNING,"INFO >> Please select yes or no",bcolors.ENDC)

    
    print(bcolors.OKBLUE,f"INFO >> Updating {mcm_id} with Daryl instructions and steps",bcolors.ENDC)
    
    mcm_overview_append = f"""
###Lock MCM
```
/apollo/env/Daryl/bin/darylscriptc --lock --cm {mcm_id}
 ```

###Dry-run
```
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode dryrun --no-auto-dashboard --no-hds
 ```

###Execute MCM
```
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode execute
```

###Variable File

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/{mcm_id}_{args.device}.var
    
    """
    
    mcm_overview_final = mcm_overview + mcm_overview_append 

    mcm_steps = [{'title':'Daryl Info','time':300,'description':f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/{mcm_id}_{args.device}.var'}]
    
    #call function to update MCM
    mcm.mcm_update(mcm_id,mcm_uid,mcm_overview_final,mcm_steps)
    print(bcolors.BOLD,f"INFO >> {mcm_id} succesfully updated, please lock the MCM through DARYL and submit for apporvals",bcolors.ENDC)

def main():
	args = parse_args()
	slot_check(args)
	linecard_mcm(args)

if __name__ == "__main__":
    main()
