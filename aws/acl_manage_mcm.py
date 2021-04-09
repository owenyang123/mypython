#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import sys
import os
import argparse
import git
import logging
from dxd_tools_dev.modules import mcm
from dxd_tools_dev.modules import mcm_variables

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='acl_manage_mcm.py')
    main_parser.add_argument("-pl", "--prefix_list_devices", type=str, dest="prefix_list_devices", required=True, help="Comma separated vc-car/vc-dar device names")
    main_parser.add_argument("-no_plu", "--no_prefix_list_update", default=True, action='store_false', dest="no_prefix_list_update", help="Specify -no_plu flag to not update prefix lists. Prefix list will be updated by default (if -no_plu is not specified)")
    main_parser.add_argument("-vccor", "--vc_cor_brick", type=str, dest="vc_cor_brick", help="VC_COR brick on which ACLs need to be deployed")
    main_parser.add_argument("-brtra", "--br_tra_devices", type=str, dest="br_tra_devices", help="Comma separated br-tra devices on which ACLs need to be deployed")
    main_parser.add_argument("-ae", "--ae_interfaces",  type=str, dest="ae_interfaces", help="Comma separated ae interfaces - e.g ae30,ae31")
    main_parser.add_argument("-dae", "--dx2_ae_interfaces", type=str, dest="dx2_ae_interfaces", help="Comma separated ae interfaces toward vc-bdr - e.g ae30,ae31")
    main_parser.add_argument("-bp", "--bgp_prestaged", type=str, default="True", help="set to True if BGP is prestaged, else False. Default is True")
    main_parser.add_argument("-sb", "--ssh_bastion", type=str, dest="ssh_bastion", required=True, help="SSH BASTION e.g neteng-bastion-iad-6004.iad6.amazon.com")
    main_parser.add_argument("-adv", "--add_devices", default=False, action='store_true', dest="add_devices", help="Optional - use this flag for adding devices to ACL Manage")
    return main_parser.parse_args()

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

    logging.info('Checking User provided input devices')

    if not cli_arguments.ae_interfaces and not cli_arguments.dx2_ae_interfaces:
        print( '-ae/--ae_interfaces and -dae/--dx2_ae_interfaces are missing. you need to specify atleast one')
        raise

    if cli_arguments.vc_cor_brick and cli_arguments.br_tra_devices:
        logging.error('vc-cor and br-tra both passed as arguments. Please specify either vc-cor or br-tra and re-run the script. Existing')
        sys.exit()

    for device in cli_arguments.prefix_list_devices.split(','):
        if not re.match('.*-vc-(car|dar|bdr)-.*', device):
            raise ValueError('Device not supported. {} must be VC-CAR or VC-DAR or VC-BDR'.format(cli_arguments.vc_car_dar_devices))

    if cli_arguments.vc_cor_brick:
        if not re.search('^[a-z][a-z][a-z][0-9][0-9]?-vc-cor-b[0-9]$',cli_arguments.vc_cor_brick):
            raise ValueError('Specify vc-cor brick. It should follow {site}-vc-cor-b{brick_number} standard')
        deploy_acl_devices = cli_arguments.vc_cor_brick + '-r1,' + cli_arguments.vc_cor_brick + '-r2,' + cli_arguments.vc_cor_brick + '-r3,' + cli_arguments.vc_cor_brick + '-r4'

    if cli_arguments.br_tra_devices:
        for device in cli_arguments.br_tra_devices.split(','):
            if not re.match('.*-br-tra-.*', device):
                raise ValueError('Device not supported. {} must be comma separated br-tra'.format(cli_arguments.br_tra_devices))
        deploy_acl_devices = cli_arguments.br_tra_devices




    logging.info('Creating variable file')
    ae_interfaces = ''
    dx2_ae_interfaces = ''
    
    devices_vc_car_dar_bdr = cli_arguments.prefix_list_devices
    ssh_bastion = cli_arguments.ssh_bastion
    add_devices = cli_arguments.add_devices
    if cli_arguments.ae_interfaces:
        ae_interfaces = cli_arguments.ae_interfaces
    if cli_arguments.dx2_ae_interfaces:
        dx2_ae_interfaces = cli_arguments.dx2_ae_interfaces
    bgp_prestaged = cli_arguments.bgp_prestaged

    car_dar_counter = 0
    bdr_counter = 0

    for device in devices_vc_car_dar_bdr.split(','):
        if 'car' in device or 'dar' in device:
            car_dar_counter += 1
        elif 'bdr' in device:
            bdr_counter += 1

    if car_dar_counter != 0:
        no_prefix_list_update = cli_arguments.no_prefix_list_update
    else:
        no_prefix_list_update = False

    variable_file = mcm_variables.create_variables_vc_cor_acl_manage(no_prefix_list_update,devices_vc_car_dar_bdr,deploy_acl_devices,ae_interfaces,dx2_ae_interfaces,ssh_bastion,add_devices,bgp_prestaged)
    logging.info('variable file created')

    logging.info('Creating MCM')

    if bdr_counter == 0:
        mcm_info = mcm.mcm_creation("acl_manage",no_prefix_list_update,devices_vc_car_dar_bdr,deploy_acl_devices)
    else:    
        mcm_info = mcm.mcm_creation("dx2_acl_manage",no_prefix_list_update,devices_vc_car_dar_bdr,deploy_acl_devices)
    mcm_id = mcm_info[0]
    mcm_uid = mcm_info[1]
    mcm_overview = mcm_info[2]
    logging.info('https://mcm.amazon.com/cms/{} created'.format(mcm_id))

    logging.info('Updating variable file with MCM number')
    variable_file_updated = variable_file.replace('MCM_NUMBER',mcm_id)
    logging.info('variable file updated')

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
    with open(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var','w') as var_file:
        var_file.write(variable_file_updated)
        var_file.close()

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
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode execute
```

###Variable File

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/{mcm_id}/{mcm_id}.var

    """
    # update MCM overview and steps
    mcm_overview_final = mcm_overview + mcm_overview_append
    mcm_steps = [{'title':'Daryl Info','time':300,'description':f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/{mcm_id}/{mcm_id}.var'}]
    mcm.mcm_update(mcm_id,mcm_uid,mcm_overview_final,mcm_steps)
    logging.info('{} successfully updated, please lock the MCM through Daryl and submit for approvals\n'.format(mcm_id))

if __name__ == '__main__':
    main()
