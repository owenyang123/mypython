#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from isd_tools_dev.modules import hercules
import sys
import logging
import argparse
import re
import os
import subprocess
from subprocess import PIPE,STDOUT
import time
import json
from dxd_tools_dev.modules import nsm
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from dxd_tools_dev.modules import mcm



def check_hercules(device,config_regex,result):
    null = open('/dev/null', 'w')

    result[str(device)] = ["error","error"]
    try:
        completed_process = subprocess.run('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file set-config --uncensored'.format(device),shell=True,stdout=subprocess.PIPE,stderr=null)
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


def bundle_prefix_list(hostnames,prefix, device_regex):
    #global generate_command,bundle_id,alfred_link
    if 'vc-car' in device_regex:
        generate_command = []
        for host in hostnames:
            alfred_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern "/{}/"  --approvers dx-deploy-l1-appro  --policy dx-update-amazongo-prefix.yaml --policy-args-file {}.var --local-file {}.cfg --batch-size 5'.format(host,prefix.split('/')[0],prefix.split('/')[0])
            if alfred_command not in generate_command:
                generate_command.append(alfred_command)
        bundle_id = []
        alfred_link = []
        for cmd in generate_command:
            try:
                print(f"\nCreating Alfred Bundle:\n{cmd}")
                output_bytes = subprocess.check_output(cmd, shell=True)
                output = output_bytes.decode("utf-8")
                bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
                bundle_number = bundle_number.split()[0]
                if cmd not in bundle_id:
                    bundle_id.append(bundle_number)
                    alfred_link.append(f"https://hercules.amazon.com/bundle-v2/{bundle_number}")
                    print(f"\nBundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")
            except subprocess.CalledProcessError:
                sys.exit("\nProblem occured while creating the bundle. Please run ReleaseWorkflowCLI with -ro and then try again!!!!!")

    elif 'vc-cor' in device_regex:
        generate_command = []
        for host in hostnames:
            alfred_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern "/{}/"  --approvers dx-deploy-l1-appro   --policy aws-dx-whitelist.yaml --policy-args-file {}.var --modules prefixlist-IPV4-AWS-DX-CUST-ALLOCATIONS --batch-size 5'.format(host,prefix.split('/')[0],prefix.split('/')[0])  

            if alfred_command not in generate_command:
                generate_command.append(alfred_command) 

        bundle_id = []
        alfred_link = []
        for cmd in generate_command:
            try:
                print(f"\nCreating Alfred Bundle:\n{cmd}")
                output_bytes = subprocess.check_output(cmd, shell=True)
                output = output_bytes.decode("utf-8")
                bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
                bundle_number = bundle_number.split()[0]
                if cmd not in bundle_id:
                    bundle_id.append(bundle_number)
                    alfred_link.append(f"https://hercules.amazon.com/bundle-v2/{bundle_number}")
                    print(f"\nBundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")
            except subprocess.CalledProcessError:
                sys.exit("\nProblem occured while creating the bundle. Please run ReleaseWorkflowCLI with -ro and then try again!!!!!")

    else:
        print('Devices not supported!')
        exit()

    return generate_command,bundle_id,alfred_link



def check_alarm(vc_host, result, region, device_regex ):
    null = open('/dev/null', 'w')
    if 'vc-car' in device_regex:
        autocheck_command = f'''/apollo/env/NetengAutoChecks/bin/autochecks_manager --checks general.check_no_chassis_alarms --target {vc_host} --ignore "PEM 3 Input Failure,Backup RE Active,PEM 3 Dipswitch 1 Feed Connection 1,PEM 1 Dipswitch 1 Feed Connection 1,PEM 3 Dipswitch 1 Feed Connection 1,PEM 1 Dipswitch 1 Feed Connection 1"'''
        command = f"ssh nebastion-{region.lower()} '{autocheck_command}'"
        autocheck_output = subprocess.run(command, shell=True,stdout=subprocess.PIPE,stderr=STDOUT).stdout.decode()
        #autocheck_output = subprocess.check_output(command, shell=True)
        if 'Check general.check_no_chassis_alarms: PASS' in autocheck_output:
            result[vc_host].append('Pass')
        else:
            result[vc_host].append('Fail')

    elif 'vc-cor' in device_regex:
        autocheck_command = f'''/apollo/env/NetengAutoChecks/bin/autochecks_manager --checks general.check_no_chassis_alarms --target {vc_host} '''
        command = f"ssh nebastion-{region.lower()} '{autocheck_command}'"
        autocheck_output = subprocess.run(command, shell=True,stdout=subprocess.PIPE,stderr=STDOUT).stdout.decode()
        #autocheck_output = subprocess.check_output(command, shell=True)
        if 'Check general.check_no_chassis_alarms: PASS' in autocheck_output:
            result[vc_host].append('Pass')
        else:
            result[vc_host].append('Fail')

    return result

def get_devices(device_regex,region):
    print("\n=========Getting All Devices Please wait========\n")
    devices_list_op = nsm.get_devices_from_nsm(device_regex,region,"OPERATIONAL")
    devices_list_ma = nsm.get_devices_from_nsm(device_regex,region,"MAINTENANCE")
    devices_list = devices_list_op + devices_list_ma
    return devices_list

def creat_config_file(prefix):
    with open("{}.cfg".format(prefix.split('/')[0]), "w") as f:
        f.write("policy-options { prefix-list AMAZON-INTERNAL-CUST-AGGREGATES { "+prefix+"; }}")


def creat_var_file(prefix, device_regex):
    with open("{}.var".format(prefix.split('/')[0]), "w") as f:
        if 'vc-car' in device_regex:
            f.write(f"PREFIX={prefix}\nPREFIX_LIST_NAME=AMAZON-INTERNAL-CUST-AGGREGATES\nIGNORE_ALARMS=PEM 3 Input Failure,Backup RE Active,PEM 3 Dipswitch 1 Feed Connection 1,PEM 1 Dipswitch 1 Feed Connection 1,PEM 3 Dipswitch 1 Feed Connection 1,PEM 1 Dipswitch 1 Feed Connection 1")
        elif 'vc-cor' in device_regex:
            f.write(f"PREFIX={prefix}\nPREFIX_LIST_NAME=IPV4-AWS-DX-CUST-ALLOCATIONS")

        else:
            print('device not supported')
            exit()

def dx_update_prefix():
    parser = argparse.ArgumentParser(description='This script will create mcms to update the amazon-go prefix list of vc-cars ')
    parser.add_argument('--device_regex', help='''specifiy the device regex in NSM  please use quotes for example "name:/dub2.*vc-edg-r22[123]/" ''')
    parser.add_argument('--prefix', help='''specifiy the prefix for example 43.224.76.0/22  ''')
    parser.add_argument('--region', help='specifiy the region ')
    parser.add_argument('--jbcr', help='specifiy the JB CR')


    args = parser.parse_args()

    REGIONS = ['iad', 'pdx', 'bjs', 'fra', 'bom', 'hkg', 'nrt', 'cmh', 'arn', 'dub','syd', 'lhr', 'pek', 'yul', 'kix', 'corp', 'cdg', 'bah', 'zhy', 'sfo','sin', 'icn', 'gru', 'cpt', 'mxp']


    if args.device_regex and args.prefix and args.jbcr and args.region in REGIONS :

        devices = get_devices(args.device_regex,args.region)
        print("\n\n")
        print(devices)
        print("\n\n")
        result = {}
        if 'vc-car' in args.device_regex:
            config_regex = f"set policy-options prefix-list AMAZON-INTERNAL-CUST-AGGREGATES {args.prefix}"
        elif 'vc-cor' in args.device_regex:
            config_regex = f"set policy-options prefix-list IPV4-AWS-DX-CUST-ALLOCATIONS {args.prefix}"
        else:
            print('device not supported')
            exit()

        with ThreadPoolExecutor(max_workers=10) as executor:
            f = {executor.submit(check_hercules,device,config_regex,result) for device in devices }
            for future in concurrent.futures.as_completed(f):
                result = future.result()


        result2 ={}
        for device in result.keys():
            if result[device][0] == "Not Found":
                result2[device] = []



        with ThreadPoolExecutor(max_workers=10) as executor:
            f = {executor.submit(check_alarm,vc_host, result2, args.region, args.device_regex) for vc_host in result2.keys() }
            for future in concurrent.futures.as_completed(f):
                result2 = future.result()

        list_of_devices = []
        hostnames = []
        devices = []
        for device in result2.keys():
            if result2[device][0] == "Pass":
                devices.append(device)
            else:
                print(f'bad alarm {device}')




        #for vc-router in devices:

        list_of_devices = [ devices[vc:vc + 10] for vc in range(0, len(devices), 10)]

        for LIST in list_of_devices:
            hostnames.append("|".join(LIST))


        creat_config_file(args.prefix)
        creat_var_file(args.prefix, args.device_regex)

        generate_command,bundle_id,alfred_link = bundle_prefix_list(hostnames, args.prefix, args.device_regex) 


        mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("dx_mcm_title_overview_prefix_list_update",devices,args.device_regex,args.jbcr,args.region)
        if mcm_id:
            print(f"\nCreated {mcm_id}.\n")
            mcm_overview += "####Bundle Generation:\n{}\n\n####Bundle Diffs/Config/Autochecks:\n{}\n".format('\n\n'.join(generate_command), '\n'.join(alfred_link))

            steps = []
            step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
            step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
            steps.append(step_ixops)
            steps.append(step_netsupport)
            for bundle in range(len(bundle_id)):
                step = {'title':f'Alfred Bundle Deployment for {args.region}','time':60,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_id[bundle]} --disable-auto-full-rollback', 'rollback':f'/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>\n makes sure provisioning goes back to orginal state using https://bladerunner.amazon.com/workflows/VeracityCLI/versions/prod'}
                steps.append(step)
            if 'vc-car' in args.device_regex:
                steps.append({'title':f' remove andoncord for {args.region}','time':10, 'description':f'/apollo/env/HerculesUtilitiesCLI/bin/hercules-utilities.sh {args.region}  andon-cord list | grep <alias> \n /apollo/env/HerculesUtilitiesCLI/bin/hercules-utilities.sh {args.region} andon-cord delete <andoncord>'})
            print(f"Updating {mcm_id} ...", end = '')
            mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
            print("MCM is created successfully. https://mcm.amazon.com/cms/{}".format(mcm_id))  

        else:
            print("\nIssue creating the MCM.")
    else:
        print("error: not all flags specified")
        parser.print_help()
        return


if __name__ == "__main__":
	dx_update_prefix()
