#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

'''
    Script to create VAR file for vc_reserve_interfaces.yaml during port reservation on br-tra
    https://code.amazon.com/packages/NetEngAutoChecksPolicies/blobs/mainline/--/configuration/etc/neteng_autochecks_policies/vc_reserve_interfaces.yaml
    ## *** Example Arguments ***
    ## INTERFACES=xe-0/0/0,xe-0/0/1
    ## LAGS=ae104,ae105
    ## CHECK_LAG_NOT_EXISTS=false
    ## CHECK_INTERFACE_STATE=false
    ## IGNORE_ALARMS=false
    ## ALARMS_TO_IGNORE=
    ## CHECK_ALL_ALARMS=true
    ## CHECK_TRAFFIC=true
    ## CHECK_INTERFACES_NOT_IN_LAG=true
    ## UPDATE_PROVISIONING=false
    ## OPER_STATUS_BEFORE=up/down as needed
    ## OPER_STATUS_AFTER=up/down as needed
    ## REGEXSTRING=string to match ex: TURNDOWN
    ## CHECK_DESCRIPTION_REGEX=true

    Once the script is executed, it will create <device_name>-port-resv.var variable file
    
    Usage
    --------
    Script Usage:
        br_tra_var.py -f < br-tra csv file >
        ex: br_tra_var.py -f "test_bjs.csv"

'''
import argparse
import collections
import itertools
import yaml
import sys
import os



parser = argparse.ArgumentParser(description="Reads csv file to create VAR file for br-tra port reservation", add_help=True)
parser.add_argument("--f", "--file", help = "Input CSV file for BR_TRA port reservation", type=str, required=True)
args= parser.parse_args()

user_id = os.getlogin()


file_name = args.f

with open(file_name,'r') as file:
    outfile = [(csv.split(',')[0], csv.split(',')[1], csv.split(',')[2]) for csv in file.readlines()][1:]

default_dict_holder = collections.defaultdict(list)

for data in outfile:
    default_dict_holder[data[0]].append(data[1:])


intf_dict = {}

def create_intf_dict(): 
    for device, params in default_dict_holder.items():
        intf_dict[device] = {}
        itertool_params = list(itertools.chain(*params))
        intf_dict[device]['INTERFACES'] = [intf for intf in itertool_params if 'et-' in intf or 'xe-' in intf]
        intf_dict[device]['LAGS'] = list(set([lag for lag in itertool_params if 'ae' in lag]))
        intf_dict[device]['CHECK_LAG_NOT_EXISTS'] = 'true'
        intf_dict[device]['CHECK_INTERFACE_STATE'] = 'true'
        intf_dict[device]['IGNORE_ALARMS'] = 'true'
        intf_dict[device]['CHECK_ALL_ALARMS'] = 'false'
        intf_dict[device]['CHECK_TRAFFIC'] = 'true'
        intf_dict[device]['UPDATE_PROVISIONING'] = 'false'
        intf_dict[device]['OPER_STATUS_BEFORE'] = 'down'
        intf_dict[device]['OPER_STATUS_AFTER'] = 'down'


def create_var_files():
    for device,var_params in intf_dict.items():
        with open('/home/{}/{}-port-resv.var'.format(user_id,device),'w') as outfile:
            yaml.dump(var_params,outfile)
        with open('/home/{}/{}-port-resv.var'.format(user_id,device)) as var_file:
            data = var_file.read()
            data = data.replace(': ','=')
            data = data.replace('[','')
            data = data.replace(']','')
            data = data.replace('= ','=')
            data = data.replace(', ',',')
            data = data.replace('\'t','t')
            data = data.replace('\'f','f')
            data = data.replace('e\'','e')
        with open('/home/{}/{}-port-resv.var'.format(user_id,device), 'w') as f:
            f.writelines(data)

if __name__ == "__main__":
   create_intf_dict()
   create_var_files()
