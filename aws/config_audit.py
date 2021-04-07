#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from isd_tools_dev.modules import hercules
import sys
import logging
import argparse
import re
import os
import subprocess
import time
import json
from dxd_tools_dev.modules import nsm
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

logs_config_audit = open("logs.txt","w")


def check_hercules(device,config_regex,result):
    result[str(device)] = ["error","error"]
    try:
        completed_process = subprocess.run('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file set-config --uncensored'.format(device),shell=True,stdout=subprocess.PIPE,stderr=logs_config_audit)
        config = completed_process.stdout.decode('ascii').splitlines()
    except Exception as e:
        log_error = "Could not get config info from Hercules of  {}".format(device)
        logging.error(log_error)
        logging.error(e)
        sys.exit()
    for config_line in config:
        if re.search(config_regex, config_line):
            example = config_line
            result[device][1] = example
            result[device][0] = "Found"
            break
        else:
            result[device][1] = "None"
            result[device][0] = "Not Found"
    return result



def print_result(result):
    print("{:<50} {:<50} {:<50}".format('Device','config specified','Example'))
    print("{:<50} {:<50} {:<50}".format('-------','----------------','-------'))
    for device in result.keys():
        print("{:<50} {:<50} {:<50}".format(device,result[device][0], result[device][1]))






def get_devices(device_regex,region):
    print("\n=========Getting All Devices Please wait========\n")
    devices_list_op = nsm.get_devices_from_nsm(device_regex,region,"OPERATIONAL")
    devices_list_ma = nsm.get_devices_from_nsm(device_regex,region,"MAINTENANCE")
    devices_list = devices_list_op + devices_list_ma
    return devices_list








def config_audit():
    parser = argparse.ArgumentParser(description='This script will get the regex config specified in a devices regex ')
    parser.add_argument('--device_regex', help='''specifiy the device regex in NSM  please use quotes for example "name:/dub2.*vc-edg-r22[123]/" ''')
    parser.add_argument('--config_regex', help='''specifiy the config regex please use quotes for example "host-name"  ''')
    parser.add_argument('--region', help='specifiy the config regex ')

    parser.add_argument('--pw', help=argparse.SUPPRESS)
    args = parser.parse_args()

    REGIONS = ['iad', 'pdx', 'bjs', 'fra', 'bom', 'hkg', 'nrt', 'cmh', 'arn', 'dub','syd', 'lhr', 'pek', 'yul', 'kix', 'corp', 'cdg', 'bah', 'zhy', 'sfo','sin', 'icn', 'gru', 'cpt', 'mxp']


    if args.device_regex and args.config_regex and args.region in REGIONS :

        devices = get_devices(args.device_regex,args.region)
        print("\n\n")
        print(devices)
        print("\n\n")
        user_input = input("\nDo Devices above is the devices you are looking for enter Yes to continue, else enter No and change devices regex! \n")
        if user_input == "Yes":
            print("\n=========Getting Devices Config Please wait========\n")
            result = {}
            with ThreadPoolExecutor(max_workers=50) as executor:
                f = {executor.submit(check_hercules,device,args.config_regex,result) for device in devices }
                for future in concurrent.futures.as_completed(f):
                    result = future.result()
            print_result(result)
            logs_config_audit.close()
        else:
            print("\n User Requested to exit\n")
            logs_config_audit.close()
            sys.exit()

    else:
        print("error: not all flags specified")
        parser.print_help()
        return

if __name__ == "__main__":
	config_audit()