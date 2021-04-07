#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import (jukebox,nsm,hercules,mcm)
import collections
import re
import subprocess
import argparse
import sys
import re
import os
import yaml
import jinja2
import concurrent.futures
from time import perf_counter
from jinja2 import Template

'''
This is the dev version mplsudp script. This is used only for testing purpose, will not be used in prod.

usage: mcm_mplsoudp.py [-h] -d

Script for scaling on vc devices towards border

optional arguments:
  -h, --help      show this help message and exit
  -d , --device_list   DEVICE NAME

Author  :   anudeept@
Version :   1.0
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
    parser.add_argument("-r","--rebase",action="store_true",help="OPTION TO REBASE")
    parser.add_argument("-t","--traffic_above",action="store_true",help="TRAFFIC THRESHOLD ABOVE PARAMETER EX: 100")
    return parser.parse_args()

def concurr_f(func, xx: list, *args, **kwargs) -> list:
    """This is the concurrency function to use multithreading

    Args:
        func ([type]): Any function to be passed
        xx (list): List of devices

    Returns:
        list: Final list
    """    
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        device_info = {executor.submit(func, x, *args, **kwargs): x for x in xx}
        for future in concurrent.futures.as_completed(device_info):
            _ = device_info[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                pass
    return f_result if f_result else None

def get_device_loopback(device):
    """This function gets the device loopback

    Args:
        device ([str]): device name

    Returns:
        loopback_ip (string) : Loopback ip address of the device
        device_info.loopback (list) : List of links the device connects to
    """
    try:
        device_info = jukebox.DeviceOverview(device)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()   
    #get device loopback and device links
    loopback_ip = str(device_info.loopback)
    loopback_dict =  {}
    loopback_dict[device] = loopback_ip
    return loopback_dict

def get_device_link(device):
    """This function gets the device link information from Jukebox

    Args:
        device ([str]): device name

    Returns:
        loopback_ip (string) : Loopback ip address of the device
        device_info.loopback (list) : List of links the device connects to
    """
    try:
        device_links = jukebox.get_device_link(device)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()    
    #get device loopback and device links
    device_links_dict = {}
    device_links_dict[device] = device_links
    return device_links_dict

def get_hercules_config(device):
    """This function fetches hercules config in set format.

    Args:
        device ([string]): device name, ex: fra50-vc-car-r1
    
    Returns:
        Device config from hercules in set format
    """    
    try:
        raw_config=hercules.get_latest_config_for_device(device,stream='collected',file_list=['set-config']).decode("utf-8").split("\n")
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    raw_config_dict = {}
    raw_config_dict[device] = raw_config
    return raw_config_dict

def mplsudp_prestage_config_mcm(device_list,rebase_flag=None,traffic_above=None):
    """This function generates yaml file for a device and renders the yaml file to generate junos config, bundle
    VAR file and MCM

    Args:
        device_list (list): list of devices

    """
    contain = collections.defaultdict(list)
    for device in device_list:
        sep = device.rsplit('-', 1)
        contain[sep[0]].append(sep[1])
    regex = ""
    for k,v in contain.items():
        regex = "{}-({})".format(k, '|'.join(v))

    device_type = []
    for hostname in device_list:
        try:
            dev_reg = re.search(r'(edg|bar|cir|car).*[0-9]$',hostname)
            device_type.append(dev_reg.group(1))
        except Exception as error:
            print(bcolors.FAIL,f"[Error] : {error}",bcolors.ENDC)
            sys.exit()

    device_type = list(set(device_type))
    device_code = ''.join(device_type)
    site_list = []
    for device in device_list:
        site_list.append(device.split('-vc')[0])
    site_code = ''.join(list(set(site_list)))
    username = os.getlogin()
    main_path = f'/home/{username}/MPLSoUDP_CONF_TEST'
    site_path = f'{main_path}/{site_code}'
    print(bcolors.OKBLUE,f'[Info] : Creating {main_path} directory',bcolors.ENDC)
    dir_check = os.path.isdir(main_path)
    if dir_check == True:
        print(bcolors.OKGREEN,f'[Info] : {main_path} directory exists, proceeding',bcolors.ENDC)
    else:
        os.mkdir(main_path)
    dir_check_site = os.path.isdir(site_path)
    if dir_check_site == True:
        print(bcolors.OKGREEN,f'[Info] : {site_path} directory exists, proceeding',bcolors.ENDC)
    else:
        os.mkdir(site_path)
    #J2 directory
    templateLoader = jinja2.FileSystemLoader(searchpath="/apollo/env/DXDeploymentTools/mplsudp_templates")
    templateEnv = jinja2.Environment(loader=templateLoader,autoescape=True)

    loopback_info, link_info, config_info = concurr_f(get_device_loopback, device_list), concurr_f(get_device_link, device_list), concurr_f(get_hercules_config, device_list)

    if len(loopback_info) == len(link_info) == len(config_info):
        for device in device_list:
            upstream_routers = []
            for dict_info in loopback_info:
                for k,v in dict_info.items():
                    if device == k:
                        try:
                            loopback_ip = dict_info[device]
                        except Exception as error:
                            print(bcolors.FAIL,f'[Error]: {error}')
                            sys.exit()

            for dict_info in link_info:
                for k,v in dict_info.items():
                    if device == k:
                        try:
                            device_links = dict_info[device]
                        except Exception as error:
                            print(bcolors.FAIL,f'[Error]: {error}')
                            sys.exit()

            for dict_info in config_info:
                for k,v in dict_info.items():
                    if device == k:
                        try:
                            raw_config = dict_info[device]
                        except Exception as error:
                            print(bcolors.FAIL,f'[Error]: {error}')
                            sys.exit()

            try:
                for hostname in device_links:
                    upstream_reg = re.search(r'(br-tra|vc-bar|vc-cor|vc-dar|vc-fab|br-agg).*[0-9]$',hostname[0])
                    if upstream_reg != None:
                        upstream_routers.append(hostname[0])
            except Exception as error:
                print(bcolors.FAIL,f'[Info] : {error}',bcolors.ENDC)
                sys.exit()

            upstream_devices = ','.join(upstream_routers)
            #upstream lag list
            upstream_ae = []

            #device dictionary mapping
            device_dict = {}
            device_dict['upstream_lag']  = {}
            device_dict['bgp_group'] = {}

            external_bgp_groups = []

            # get ebgp peer groups from config
            for line in raw_config:
                if re.match(f"set protocols bgp group .* type external",line):
                    group_name = line.split('type')[0].split('group')[1].strip()
                    if 'CSC' in group_name or 'csc' in group_name or 'FAB' in group_name or 'fab' in group_name or 'BAR' in group_name or 'bar' in group_name:
                        external_bgp_groups.append(group_name)

            #delete groups which are inactive
            for group in external_bgp_groups:
                for line in raw_config:
                    if re.match(f"deactivate protocols bgp group {group}",line):
                        external_bgp_groups.remove(group)

            #update device_dict with bgp group and policies
            for group in external_bgp_groups:
                device_dict['bgp_group'][group] = {}
                for line in raw_config:
                    if re.match(f"set protocols bgp group {group} import",line):
                        import_policy = line.split('import')[1].strip()
                        device_dict['bgp_group'][group]['import_policy'] = import_policy
                    if re.match(f"set protocols bgp group {group} export",line):
                        export_policy = line.split('export')[1].strip()
                        device_dict['bgp_group'][group]['export_policy'] = export_policy

            #update device_dict with vc-car upstream lag
            for line in raw_config:
                if re.match(f"set interfaces ae.* description .*-(br-tra|vc-cor|vc-dar|vc-fab|br-agg|vc-bar)-",line):
                    if "unit" not in line:
                        ae_num = line.split('description')[0].split('interfaces')[1].strip()
                        device_dict['upstream_lag'][ae_num] = {}
                        for new_line in raw_config:
                            if re.match(f"set interfaces {ae_num} unit 10 family inet mtu",new_line):
                                mtu = new_line.split('mtu')[-1].strip()
                                device_dict['upstream_lag'][ae_num]['mtu'] = mtu
                            elif re.match(f"set interfaces {ae_num} mtu",new_line):
                                mtu = new_line.split('mtu')[-1].strip()
                                device_dict['upstream_lag'][ae_num]['mtu'] = mtu

            print(bcolors.OKBLUE,f'[Info] : Getting loopback address for {device} from Jukebox',bcolors.ENDC)

            device_dict['loopback'] = loopback_ip

            path = f'{site_path}/{device}'
            print(bcolors.OKBLUE,f'[Info] : Creating {path} directory',bcolors.ENDC)
            dir_check = os.path.isdir(path)
            if dir_check == True:
                print(bcolors.OKGREEN,f'[Info] : {path} directory exists, proceeding')
            else:
                os.mkdir(path)

            try:
                with open(f'{path}/{device}.yaml','w') as outfile:
                    outfile.write(yaml.dump(device_dict,default_flow_style=False ))
            except Exception as error:
                print(bcolors.FAIL,f'[Error] : {error}')
                sys.exit()

            if device_code == 'edg':
                j2 = "vc_edg.j2"
            elif device_code == 'car':
                j2 = 'vc_car.j2'
            elif device_code == 'cir':
                j2 = 'vc_cir.j2'

            template = templateEnv.get_template(j2)
            yaml_file = yaml.safe_load(open(f'{path}/{device}.yaml'))
            #generate conf
            print(bcolors.OKBLUE,f'[Info] : Generating config/VAR for {device}',bcolors.ENDC)
            try:
                with open(f'{path}/{device}.conf','w') as device_config:
                    print(template.render(yaml_file),file=device_config)
            except Exception as error:
                print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
                sys.exit()

            with open(f'{path}/{device}.var','w') as var_file:
                var_file.write(f'IGNORE_ALARMS=PEM 0 Input Failure,PEM 0 Not OK,PEM 1 Input Failure,PEM 1 Not OK,PEM 2 Input Failure,PEM 2 Not OK,PEM 3 Input Failure,PEM 3 Not OK,Backup RE Active,Loss of communication with Backup RE\n')
                var_file.write(f'traffic_threshold_below=2000\n')
                if traffic_above:
                    var_file.write(f'traffic_threshold_above={traffic_above}\n')
                else:
                    var_file.write(f'traffic_threshold_above=2000\n')
                var_file.write(f'loopback={loopback_ip}\n')

            print(bcolors.OKGREEN,f'[Info] : Config/VAR file saved to {path}',bcolors.ENDC)

    bundle_commands = []
    bundle_dict = {}
    
    for device in device_list:
        path = f'/home/{username}/MPLSoUDP_CONF/{device}'
        if device_code == 'edg':
            bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --local-files {device}.conf --policy dx_deploy_mplsudp.yaml --policy-args-file {device}.var  --approvers l1-approver --tshift'
        elif device_code == 'car' or device_code == 'cir':
            if rebase_flag:
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --policy dx_deploy_mplsudp.yaml --policy-args-file {device}.var  --approvers l1-approver -m all --tshift'
            else:
                bundle_command = f'cd {path} && /apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {device} --local-files {device}.conf --policy dx_deploy_mplsudp.yaml --policy-args-file {device}.var  --approvers l1-approver'
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
        mcm_create = mcm.mcm_creation("mcm_title_overview_prestage_mplsoudp",device_list,regex,site_code)
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
            device_name = command.split('--devices')[1].split('--local-files')[0].strip()
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

def main():
    start_time = perf_counter()
    args = parse_args()
    device_type = []
    #Validating user arguments
    for device in args.devices:
        device_type.append(re.search(r"(vc|br)-([a-z][a-z][a-z])", device).group())

    device_type = list(set(device_type))
    device_code = ''.join(device_type)
    if device_code == 'vc-car' or 'vc-edg' or 'vc-cir':
        if args.rebase:
            mplsudp_prestage_config_mcm(args.devices,args.rebase)
        elif args.rebase and args.traffic_above:
            mplsudp_prestage_config_mcm(args.devices,args.rebase,args.traffic_above)
        elif args.traffic_above:
            mplsudp_prestage_config_mcm(args.devices,args.traffic_above)
        else:
            mplsudp_prestage_config_mcm(args.devices)
    else:
        print(bcolors.FAIL,f'[Error] : Could not find the device type, device type should be car/edg/cir - Exiting',bcolors.ENDC)
        sys.exit()
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
