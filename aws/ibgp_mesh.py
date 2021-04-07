#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import sys
import os
import subprocess
import argparse
import git
import logging
import math
import concurrent.futures
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from dxd_tools_dev.modules import jukebox
from dxd_tools_dev.modules import mcm
from dxd_tools_dev.modules import hercules
from dxd_tools_dev.modules import utils

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='ibgp_mesh.py')
    main_parser.add_argument("-nd", "--new-devices", type=str, dest="new_devices", required=True, help="Comma separated new device names")
    main_parser.add_argument("-sb", "--ssh-bastion", type=str, dest="ssh_bastion", help="SSH BASTION e.g neteng-bastion-iad-6004.iad6.amazon.com (Optional)")
    main_parser.add_argument("-ai", "--alarms_to_ignore", type=str, dest="alarms_to_ignore", help="Comma separated Alarms to ingore (Optional)")
    main_parser.add_argument("-aze", "--azotd_exempt", default=False,  action='store_true', dest="azotd_exempt", help="Optional This flag will put all devices in one mcm only use if you have approvals to run ibgp-mesh without following AZOTD")
    main_parser.add_argument("-md", "--max_devices_mcm", default=25, type=int, dest="max_devices_mcm", help="Maximum number of devices per MCM. Default: 25")
    return main_parser.parse_args()

def check_hercules(device,config_regex,result):
    with open(os.devnull,'wb') as DEVNULL:
        try:
            completed_process = subprocess.run('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file set-config --uncensored'.format(device),shell=True,stdout=subprocess.PIPE,stderr=DEVNULL)
            config = completed_process.stdout.decode('ascii').splitlines()
        except Exception as e:
            log_error = "Could not get config info from Hercules of  {}".format(device)
            logging.error(log_error)
            logging.error(e)
            sys.exit()
    for config_line in config:
        if re.search(config_regex, config_line):
            result.append(device)
            break
    return result

def get_devices_realm(new_devices):
    device_realm = list()

    for device in new_devices.split(','):
        device_realm.append(jukebox.get_device_detail(device).data.device.realm)

    if not (len(set(device_realm))==1):
        raise Exception('Realm of new devices do not match, quitting')
    else:
        return device_realm[0]

def get_mesh_devices(new_devices, device_list):
    mesh_devices = list()
    byte_dance_devices = ['iad66-vc-car-iad-p1-v1-r1', 'iad66-vc-car-iad-p1-v1-r2', 'iad7-vc-edg-r361', 'iad7-vc-edg-r362', 'iad7-vc-edg-r363', 'iad7-vc-edg-r364']

    if 'car' in new_devices.split(',')[0]:
        pattern = '.*-(rrr|car|agg|edg)-.*'
    elif 'cir' in new_devices.split(',')[0]:
        pattern = '.*-(rrr|edg)-.*'
    elif 'agg' in new_devices.split(',')[0]:
        pattern = '.*-(car|agg|edg)-.*'
    elif 'edg' in new_devices.split(',')[0]:
        pattern = '.*-(rrr|car|cir|agg|edg)-.*'
    elif 'rrr' in new_devices.split(',')[0]:
        pattern = '.*-(car|cir|edg)-.*'

    for device in device_list:
        if device not in new_devices.split(','):
            if re.match(pattern, device):
                mesh_devices.append(device)
    for byte_dance_device in byte_dance_devices:
        for device in mesh_devices:
            if device == byte_dance_device:
                mesh_devices.remove(byte_dance_device)
    return mesh_devices

def check_edges(mesh_devices,new_devices):
    if 'car' in new_devices.split(',')[0] or 'cir' in new_devices.split(',')[0] or 'agg' in new_devices.split(',')[0] or 'rrr' in new_devices.split(',')[0]:
        check_edge = list()
        remove_from_mesh = list()
        for device in mesh_devices:
            if "vc-edg-" in device:
                check_edge.append(device)

        region_edg_list = list()
        for edge_device in check_edge:
            region_edg_list.append(edge_device.split('-')[0])
        region_edg_list = list(set(region_edg_list))
        commercial_edg_groups_list = list()

        for region_edg in region_edg_list:
            for group in jukebox.get_site_region_details(region_edg).region.edg_groups:
                if 'ExternalCustomer' == group.edg_group_type:
                    commercial_edg_groups_list.append(group.name)
        commercial_edg_groups_list = list(set(commercial_edg_groups_list))

        for edge_device in check_edge:
            edge_device_group_name = jukebox.get_device_detail(edge_device).data.device.edg_group
            if edge_device_group_name not in commercial_edg_groups_list:
                remove_from_mesh.append(edge_device)

        for device in remove_from_mesh:
            mesh_devices.remove(device)

    else:
        check_edge = list()
        remove_from_mesh = list()
        new_device_edge_group_name  = jukebox.get_device_detail(new_devices.split(',')[0]).data.device.edg_group

        for device in mesh_devices:
            if "vc-edg-" in device:
                check_edge.append(device)

        for edge_device in check_edge:
            edge_device_group_name = jukebox.get_device_detail(edge_device).data.device.edg_group
            if edge_device_group_name != new_device_edge_group_name:
                remove_from_mesh.append(edge_device)

        for device in remove_from_mesh:
            mesh_devices.remove(device)

    filtered_mesh_devices = mesh_devices
    return filtered_mesh_devices

def get_existing_devices(ibgp_mesh_devices):
    sites = list()
    existing_devices_list = list()
    existing_devices_list_to_be_used = list()
    existing_devices = '## set EXISTING_DEVICES = [\n'

    for device in ibgp_mesh_devices:
        sites.append(device.split('-')[0])
    for site in list(set(sites)):
        site_devices_list = list()
        for device in ibgp_mesh_devices:
            if site == device.split('-')[0]:
                site_devices_list.append(device)
        existing_devices_list.append(site_devices_list)

    for device_list in existing_devices_list:
        if len(device_list) > 4:
            for devices in list(utils.chunks(device_list,4)):
                existing_devices_list_to_be_used.append(devices)
        else:
            existing_devices_list_to_be_used.append(device_list)

    for devices in existing_devices_list_to_be_used:
        if devices != existing_devices_list_to_be_used[len(existing_devices_list_to_be_used) - 1]:
            existing_devices += '\t\t' + str(devices) + ',\n'
        else:
            existing_devices += '\t\t' + str(devices) + '\n\t]\n'

    return existing_devices

def get_new_devices(new_devices):
    new_cm_devices = '## set NEW_DEVICES = [\n\t[\n'

    for device in new_devices.split(','):
        if device != new_devices.split(',')[len(new_devices.split(',')) - 1]:
            new_cm_devices += "\t\t{'Name':'" + device + "', 'Loopback':'" + jukebox.get_device_detail(device).data.device.loopback_addresses[0].ipv4_address + "'},\n"
        else:
            new_cm_devices += "\t\t{'Name':'" + device + "', 'Loopback':'" + jukebox.get_device_detail(device).data.device.loopback_addresses[0].ipv4_address + "'}\n\t]\n]\n"

    return new_cm_devices

def git_clone(package, path= "/home/" + os.getlogin() + "/"):
    full_path =  path + package
    full_url = 'ssh://git.amazon.com/pkg/' + package
    try:
        repo = git.Repo.clone_from(full_url ,to_path = f'{full_path}')
        return repo
    except:
        logging.error('Could not clone {}. Exception {}'.format(package, sys.exc_info()))
        return None

def main():
    cli_arguments = parse_args()

    if cli_arguments.max_devices_mcm > 25:
        max_devices_mcm = 25
    else:
        max_devices_mcm = cli_arguments.max_devices_mcm
        
    device_type = list()
    device_az = list()
    ibgp_mesh_devices_final_list = list()
    deactivated_devices = list()
    deactivated_devices_final_list = list()
    removed_ibgp_mesh_devices = list()

    logging.info('Checking User provided input devices')

    for device in cli_arguments.new_devices.split(','):
        if not re.match('.*-(rrr|car|cir|agg|edg)-.*', device):
            raise ValueError('Device not supported. Supported regex .*-(rrr|car|cir|agg|edg)-.*')

    for device in cli_arguments.new_devices.split(','):
        device_type.append(device.split('-')[2])
        device_az.append(device.split('-')[0])

    if len(list(set(device_type))) != 1:
        raise ValueError('Mulitple device types not supported {}'.format(cli_arguments.new_devices))

    if len(list(set(device_az))) != 1:
        raise ValueError('Devices from multiple sites not supported {}'.format(cli_arguments.new_devices))

    if list(set(device_type))[0] == 'edg':
        edg_group = list()
        for device in cli_arguments.new_devices.split(','):
            edg_group.append(jukebox.get_device_detail(device).data.device.edg_group)
        if len(list(set(edg_group))) != 1:
            raise ValueError('vc-edg {} are not from same edge group'.format(cli_arguments.new_devices))
        else:
            logging.info('vc-edg {} are from same edge group'.format(cli_arguments.new_devices))

    logging.info('User input devices verified')
    logging.info('This script may take upto ~60 minutes depending upon the region -  It fetches information from JukeBox and parses Hercules configs')
    logging.info('Fetching information from JukeBox')
    realm = get_devices_realm(cli_arguments.new_devices)
    all_devices_list = jukebox.get_devices_in_jukebox_region(realm)
    ibgp_mesh_devices_initial = get_mesh_devices(cli_arguments.new_devices, all_devices_list)
    ibgp_mesh_devices_final = check_edges(ibgp_mesh_devices_initial,cli_arguments.new_devices)
    logging.info('Information from JukeBox successfully fetched')

    logging.info('Parsing hercules config of\n{}\nto ensure\n{}\nare not configured'.format(ibgp_mesh_devices_final,cli_arguments.new_devices.split(',')))
    new_device_ips = [str(jukebox.get_device_detail(device).data.device.loopback_addresses[0].ipv4_address) for device in cli_arguments.new_devices.split(',')]

    new_devices_pattern = '.*(' + '|'.join(new_device_ips) + ').*'

    pool = Pool(16)
    devices_data = dict()
    for i in range(7):
        for device in ibgp_mesh_devices_final:
            devices_data.update({device:pool.apply_async(hercules.get_config_matching_pattern, args = (device,new_devices_pattern,))})
        for device in ibgp_mesh_devices_final:
            for line in devices_data[device].get():
                if 'import' in line:
                    devices_data[device].get().remove(line)
                if 'family' in line:
                    devices_data[device].get().remove(line)
                if 'deactivate' in line:
                    deactivated_devices.append(device)
            if devices_data[device].get():
                ibgp_mesh_devices_final.remove(device)
                removed_ibgp_mesh_devices.append(device)

    logging.info('Hercules configs parsed')

    deactivated_devices = list(set(deactivated_devices))
    deactivated_devices.sort()

    if removed_ibgp_mesh_devices:
        removed_ibgp_mesh_devices = list(set(removed_ibgp_mesh_devices))
        removed_ibgp_mesh_devices.sort()
        logging.info('{}\nwere removed as a result of parsing Hercules configs. They will not be included in MCMs'.format(removed_ibgp_mesh_devices))
    
    if ibgp_mesh_devices_final:
        if not cli_arguments.azotd_exempt:
            all_az_devices = [i for i in ibgp_mesh_devices_final if not re.match('.*-vc-(car|rrr).*',i)]
            all_pop_devices = [i for i in ibgp_mesh_devices_final if re.match('.*-vc-(car|rrr).*',i)]

            if all_pop_devices:
                if len(all_pop_devices) > max_devices_mcm:
                    start_index = 0
                    finish_index = max_devices_mcm
                    for i in range(math.ceil(len(all_pop_devices)/max_devices_mcm)):
                        ibgp_mesh_devices_final_list.append(all_pop_devices[start_index:finish_index])
                        start_index = start_index + max_devices_mcm
                        finish_index = finish_index + max_devices_mcm
                else:
                    ibgp_mesh_devices_final_list.append(all_pop_devices)

            if all_az_devices:
                all_az = sorted(set(i.split('-')[0] for i in all_az_devices))   

                for i in all_az:
                    az_devices_list = list()
                    for j in all_az_devices:
                        if i == j.split('-')[0]:
                            az_devices_list.append(j)
                    ibgp_mesh_devices_final_list.append(az_devices_list)
        else:
            ibgp_mesh_devices_final_list.append(ibgp_mesh_devices_final)

        logging.info('{} devices need to be updated, {} MCM(s) will be created'.format(int(len(ibgp_mesh_devices_final)),int(len(ibgp_mesh_devices_final_list))))
    
        for ibgp_mesh_devices_final in ibgp_mesh_devices_final_list:

            # Creating MCM
            logging.info('Creating MCM')
            mcm_info = mcm.mcm_creation("ibgp_mesh",realm,cli_arguments.new_devices,ibgp_mesh_devices_final,"regular")
            mcm_id = mcm_info[0]
            mcm_uid = mcm_info[1]
            mcm_overview = mcm_info[2]

            logging.info('https://mcm.amazon.com/cms/{} created'.format(mcm_id))

            # Creating variable file
            logging.info('Creating variable file')
            mcm_exising_devices = get_existing_devices(ibgp_mesh_devices_final)
            mcm_new_devices = get_new_devices(cli_arguments.new_devices)
            fabric_bastion = "## set FABRIC_BASTION = 'security-bastions-prod-" + realm + ".amazon.com'\n"
            region = "## set REGION = '" + realm + "'\n"
            template = "{% include 'brazil://DxVpnCMTemplates/templates/ibgp_mesh_hs.jt' %}"
            mcm_number = "## set CM = '" + mcm_id + "'\n"

            if cli_arguments.ssh_bastion:
                ssh_bastion = "## set SSH_BASTION = '" + cli_arguments.ssh_bastion + "'\n"
            else:
                ssh_bastion = "## set SSH_BASTION = '<Provide SSH bastion>'\n"

            if cli_arguments.alarms_to_ignore:
                alarms = "## set ALARMS_TO_IGNORE = '" + cli_arguments.alarms_to_ignore + "'\n"
                var_file = region + mcm_number + mcm_exising_devices + mcm_new_devices + ssh_bastion + fabric_bastion + alarms + template
            else:
                var_file = region + mcm_number + mcm_exising_devices + mcm_new_devices + ssh_bastion + fabric_bastion + template

            logging.info('Variable file successfully created')

            # git operations
            logging.info('Performing git operations')
            username = os.getlogin()
            if os.path.exists(f'/home/{username}/DxVpnCM2014/') == True:
                repo = git.Repo(f'/home/{username}/DxVpnCM2014')
                origin = repo.remote('origin')
                logging.info('DxVpnCM2014 repo exists')
                if os.path.exists(f'/home/{username}/DxVpnCM2014/cm/{username}') == True:
                    logging.info('{} exists under DxVpnCM2014/cm directory'.format(username))
                    logging.info('Performing git pull')
                    origin.pull()
                else:
                    logging.info('{} does not exists under DxVpnCM2014/cm directory'.format(username))
                    os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}')
                    logging.info('User {} successfully created user directory under DxVpnCM2014/cm'.format(username))
                    logging.info('Performing git pull')
                    origin.pull()
            else:
                logging.info('DxVpnCM2014 repo does not exist')
                logging.info('Performing git clone on DxVpnCM2014')
                cloned = git_clone('DxVpnCM2014')

                if cloned:
                    logging.info('git clone successful for DxVpnCM2014')
                    repo = git.Repo(f'/home/{username}/DxVpnCM2014')
                    origin = repo.remote('origin')
                    if os.path.exists(f'/home/{username}/DxVpnCM2014/cm/{username}') == True:
                        logging.info('{} exists under DxVpnCM2014/cm directory'.format(username))
                        logging.info('Performing git pull')
                        origin.pull()
                    else:
                        logging.info('{} does not exists under DxVpnCM2014/cm directory'.format(username))
                        os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}')
                        logging.info('User {} successfully created user directory under DxVpnCM2014/cm'.format(username))
                        logging.info('Performing git pull')
                        origin.pull()
                else:
                    logging.error('git clone failed for DxVpnCM2014. Clone DxVpnCM2014 manually and re-run the script')
                    sys.exit()

            os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}')
            with open(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var','w') as variable_file:
                variable_file.write(var_file)
                variable_file.close()

            logging.info(f'Created variable file for Daryl /home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var')
            logging.info('Prepping for variable file to be pushed to DxVpnCM2014 repo')
            repo = git.Repo(f'/home/{username}/DxVpnCM2014')
            logging.info('git add')
            repo.index.add([f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var'])
            logging.info('git status\n{}\n'.format(repo.git.status()))
            logging.info('git commit')
            repo.index.commit(f'variable file for {mcm_id}')
            origin = repo.remote('origin')
            logging.info('git push')
            origin.push()
            logging.info('variable file /home/{}/DxVpnCM2014/cm/{}/{}/{}.var successfully pushed to DxVpnCM2014 repo'.format(username,username,mcm_id,mcm_id))

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
1. "inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/)
2. Start Monitoring "Darylmon all" and #netsupport Chime Room. This is to see any ongoing/newly coming Sev2s in AWS Networking
3. /apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode execute
```

###Variable File

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/{mcm_id}/{mcm_id}.var

    """
            # update MCM overview and steps
            mcm_overview_final = mcm_overview + mcm_overview_append
            mcm_steps = [{'title':'Daryl Info','time':300,'description':f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var'}]
            mcm.mcm_update(mcm_id,mcm_uid,mcm_overview_final,mcm_steps)
            logging.info('{} successfully updated, please lock the MCM through Daryl and submit for approvals\n'.format(mcm_id))

    if deactivated_devices:
        logging.info('Devices found for activating BGP neighbors\n{}'.format(deactivated_devices))
        if not cli_arguments.azotd_exempt:
            all_az_devices = [i for i in deactivated_devices if not re.match('.*-vc-(car|rrr).*',i)]
            all_pop_devices = [i for i in deactivated_devices if re.match('.*-vc-(car|rrr).*',i)]   

            if all_pop_devices:
                if len(all_pop_devices) > max_devices_mcm:
                    start_index = 0
                    finish_index = max_devices_mcm
                    for i in range(math.ceil(len(all_pop_devices)/max_devices_mcm)):
                        deactivated_devices_final_list.append(all_pop_devices[start_index:finish_index])
                        start_index = start_index + max_devices_mcm
                        finish_index = finish_index + max_devices_mcm
                else:
                    deactivated_devices_final_list.append(all_pop_devices)  

            if all_az_devices:
                all_az = sorted(set(i.split('-')[0] for i in all_az_devices))   

                for i in all_az:
                    az_devices_list = list()
                    for j in all_az_devices:
                        if i == j.split('-')[0]:
                            az_devices_list.append(j)
                    deactivated_devices_final_list.append(az_devices_list)
        else:
            deactivated_devices_final_list.append(deactivated_devices)

        logging.info('{} devices need to be updated, {} MCM(s) will be created'.format(int(len(deactivated_devices)),int(len(deactivated_devices_final_list))))

        for ibgp_mesh_devices_final in deactivated_devices_final_list:

            # Creating MCM
            logging.info('Creating MCM')
            mcm_info = mcm.mcm_creation("ibgp_mesh",realm,cli_arguments.new_devices,ibgp_mesh_devices_final,"activate")
            mcm_id = mcm_info[0]
            mcm_uid = mcm_info[1]
            mcm_overview = mcm_info[2]

            logging.info('https://mcm.amazon.com/cms/{} created'.format(mcm_id))

            # Creating variable file
            logging.info('Creating variable file')
            mcm_exising_devices = get_existing_devices(ibgp_mesh_devices_final)
            mcm_new_devices = get_new_devices(cli_arguments.new_devices)
            fabric_bastion = "## set FABRIC_BASTION = 'security-bastions-prod-" + realm + ".amazon.com'\n"
            region = "## set REGION = '" + realm + "'\n"
            template = "{% include 'brazil://DxVpnCMTemplates/templates/ibgp_mesh_hs_activate_nei.jt' %}"
            mcm_number = "## set CM = '" + mcm_id + "'\n"

            if cli_arguments.ssh_bastion:
                ssh_bastion = "## set SSH_BASTION = '" + cli_arguments.ssh_bastion + "'\n"
            else:
                ssh_bastion = "## set SSH_BASTION = '<Provide SSH bastion>'\n"

            if cli_arguments.alarms_to_ignore:
                alarms = "## set ALARMS_TO_IGNORE = '" + cli_arguments.alarms_to_ignore + "'\n"
                var_file = region + mcm_number + mcm_exising_devices + mcm_new_devices + ssh_bastion + fabric_bastion + alarms + template
            else:
                var_file = region + mcm_number + mcm_exising_devices + mcm_new_devices + ssh_bastion + fabric_bastion + template

            logging.info('Variable file successfully created')

            # git operations
            logging.info('Performing git operations')
            username = os.getlogin()
            if os.path.exists(f'/home/{username}/DxVpnCM2014/') == True:
                repo = git.Repo(f'/home/{username}/DxVpnCM2014')
                origin = repo.remote('origin')
                logging.info('DxVpnCM2014 repo exists')
                if os.path.exists(f'/home/{username}/DxVpnCM2014/cm/{username}') == True:
                    logging.info('{} exists under DxVpnCM2014/cm directory'.format(username))
                    logging.info('Performing git pull')
                    origin.pull()
                else:
                    logging.info('{} does not exists under DxVpnCM2014/cm directory'.format(username))
                    os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}')
                    logging.info('User {} successfully created user directory under DxVpnCM2014/cm'.format(username))
                    logging.info('Performing git pull')
                    origin.pull()
            else:
                logging.info('DxVpnCM2014 repo does not exist')
                logging.info('Performing git clone on DxVpnCM2014')
                cloned = git_clone('DxVpnCM2014')

                if cloned:
                    logging.info('git clone successful for DxVpnCM2014')
                    repo = git.Repo(f'/home/{username}/DxVpnCM2014')
                    origin = repo.remote('origin')
                    if os.path.exists(f'/home/{username}/DxVpnCM2014/cm/{username}') == True:
                        logging.info('{} exists under DxVpnCM2014/cm directory'.format(username))
                        logging.info('Performing git pull')
                        origin.pull()
                    else:
                        logging.info('{} does not exists under DxVpnCM2014/cm directory'.format(username))
                        os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}')
                        logging.info('User {} successfully created user directory under DxVpnCM2014/cm'.format(username))
                        logging.info('Performing git pull')
                        origin.pull()
                else:
                    logging.error('git clone failed for DxVpnCM2014. Clone DxVpnCM2014 manually and re-run the script')
                    sys.exit()

            os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}')
            with open(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var','w') as variable_file:
                variable_file.write(var_file)
                variable_file.close()

            logging.info(f'Created variable file for Daryl /home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var')
            logging.info('Prepping for variable file to be pushed to DxVpnCM2014 repo')
            repo = git.Repo(f'/home/{username}/DxVpnCM2014')
            logging.info('git add')
            repo.index.add([f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var'])
            logging.info('git status\n{}\n'.format(repo.git.status()))
            logging.info('git commit')
            repo.index.commit(f'variable file for {mcm_id}')
            origin = repo.remote('origin')
            logging.info('git push')
            origin.push()
            logging.info('variable file /home/{}/DxVpnCM2014/cm/{}/{}/{}.var successfully pushed to DxVpnCM2014 repo'.format(username,username,mcm_id,mcm_id))

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
1. "inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/)
2. Start Monitoring "Darylmon all" and #netsupport Chime Room. This is to see any ongoing/newly coming Sev2s in AWS Networking
3. /apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode execute
```

###Variable File

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/{mcm_id}/{mcm_id}.var

    """
            # update MCM overview and steps
            mcm_overview_final = mcm_overview + mcm_overview_append
            mcm_steps = [{'title':'Daryl Info','time':300,'description':f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var'}]
            mcm.mcm_update(mcm_id,mcm_uid,mcm_overview_final,mcm_steps)
            logging.info('{} successfully updated, please lock the MCM through Daryl and submit for approvals\n'.format(mcm_id))

    if (not ibgp_mesh_devices_final) and (not deactivated_devices):
        logging.info('{} are part of iBGP mesh. No MCMs will be created. Exiting...'.format(cli_arguments.new_devices))
        sys.exit()

if __name__ == '__main__':
    main()

