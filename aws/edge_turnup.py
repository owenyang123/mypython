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
from dxd_tools_dev.modules import jukebox,az,mcm,hercules


logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='edge_turnup.py')
    main_parser.add_argument("-nd", "--new-device", type=str, dest="new_device", required=True, help="hostname of the new edge to be turned up")
    main_parser.add_argument("-sb", "--ssh-bastion", type=str, dest="ssh_bastion", help="SSH BASTION e.g neteng-bastion-iad-6004.iad6.amazon.com ")
    main_parser.add_argument("-eb", "--ec2-bastion", type=str, dest="ec2_bastion", help="EC2 SSH BASTION e.g neteng-bastion-ec2-iad-4101.z-4.aes0.internal")
    main_parser.add_argument("-bf-mcm", "--backfill-mcm", type=str, dest="backfill_mcm", help="BACKFILL MCM e.g MCM-34495070 (Optional)")
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
    vc_edg = cli_arguments.new_device
    backfill_mcm = cli_arguments.backfill_mcm
    prod_ssh_bastion = cli_arguments.ssh_bastion
    ec2_ssh_bastion = cli_arguments.ec2_bastion

    mcm_info = mcm.mcm_creation("edge_turnup",cli_arguments.new_device,cli_arguments.backfill_mcm)
    mcm_id = mcm_info[0]
    mcm_uid = mcm_info[1]
    mcm_overview = mcm_info[2]

    logging.info('https://mcm.amazon.com/cms/{} created'.format(mcm_id))

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

    os.mkdir(f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}'.format(username=username, mcm_id=mcm_id))
    path = '/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}'.format(username=username, mcm_id=mcm_id)
    logging.info('Creating variable file')
    az.generate_edg_turnup_var(mcm_id,vc_edg,backfill_mcm,prod_ssh_bastion, ec2_ssh_bastion,path=path)
    logging.info('Variable file successfully created')

    logging.info(f'Created variable file for Daryl /home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{vc_edg}.var')
    logging.info('Prepping for variable file to be pushed to DxVpnCM2014 repo')
    repo = git.Repo(f'/home/{username}/DxVpnCM2014')
    logging.info('git add')
    repo.index.add([f'/home/{username}/DxVpnCM2014/cm/{username}/{mcm_id}/{vc_edg}.var'])
    logging.info('git status\n{}\n'.format(repo.git.status()))
    logging.info('git commit')
    repo.index.commit(f'variable file for {vc_edg}')
    origin = repo.remote('origin')
    logging.info('git push')
    origin.push()
    logging.info('variable file /home/{}/DxVpnCM2014/cm/{}/{}/{}.var successfully pushed to DxVpnCM2014 repo'.format(username,username,mcm_id,vc_edg))

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

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/{mcm_id}/{vc_edg}.var

    """
    # update MCM overview and steps
    mcm_overview_final = mcm_overview + mcm_overview_append
    mcm_steps = [{'title':'Daryl Info','time':300,'description':f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/{mcm_id}/{vc_edg}.var'}]
    mcm.mcm_update(mcm_id,mcm_uid,mcm_overview_final,mcm_steps)
    logging.info('{} successfully updated, please lock the MCM through Daryl and submit for approvals\n'.format(mcm_id))   


if __name__ == '__main__':
    main()
