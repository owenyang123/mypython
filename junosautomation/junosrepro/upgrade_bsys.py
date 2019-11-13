#!/usr/bin/env python

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
from lxml import etree
from xml.dom.minidom import parse, parseString
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import yaml, argparse, jinja2
import time, logging, signal
import os, sys, re, warnings
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("host_info", type=argparse.FileType("r"),help="YAML based file containing variables.")
args = parser.parse_args()


#Interogation user if continue
def user_prompt():
    move_to_next = False
    user_response = ''
    logging.debug("Getting explicit permission to continue")
    while True:
        print("Do you want to proceed? (yes/no): ")
        user_response = raw_input('Please enter "yes" to Continue, "no" to stop: ')
        logging.debug("user response: {}\n".format(user_response))
        if user_response.lower() == 'yes':
            move_to_next = True
            return move_to_next
        elif user_response.lower() == 'no':
            move_to_next = False
            return move_to_next

#Connect/Reconnect to router
def reconnect_dev(dev, retry):
    connected = False
    for i in range(retry):
        try:
            i = i + 1
            logging.info("Reconnecting to {}, attempt {}".format(dev.hostname, i))
            dev.open()
            dev.timeout = 1800
            logging.info("Connected....")
            connected = True
            return connected
        except:
            logging.info("Cannot connect to {}".format(dev.hostname))
            logging.info("Retrying....")
            time.sleep(45)
            i += 1
    logging.info("Unable to connect to {}, Giving up....\n".format(dev.hostname))
    return connected

#Get RE info, retun a {}dict that has status: mastership-state: idle-CPU:
def get_re_info(dev):
    re_info = {}
    if not dev.connected:
        reconnect = reconnect_dev(dev, 2)
        if not reconnect:
            logging.info("Connection Failed to {}\n".format(dev.hostname))
            return re_info, master_info
    get_re = dev.rpc.get_route_engine_information()
    for RE in get_re.findall('route-engine'):
        re_info[RE.find('slot').text] = {}
        try:
            re_info[RE.find('slot').text]['status'] = RE.find('status').text
        except:
            re_info[RE.find('slot').text]['status'] = 'NOK'
        try:
            re_info[RE.find('slot').text]['mastership-state'] = RE.find('mastership-state').text
            if RE.find('mastership-state').text == 'backup':
                master_info['backup'] = "re{}".format(RE.find('slot').text)
            elif RE.find('mastership-state').text == 'master':
                master_info['master'] = "re{}".format(RE.find('slot').text)
        except:
            re_info[RE.find('slot').text]['mastership-state'] = 'NA'
        try:
            re_info[RE.find('slot').text]['cpu-idle'] = RE.find('cpu-idle').text
        except:
            re_info[RE.find('slot').text]['cpu-idle'] = 'NA'
    return re_info, master_info

#Write output to the file
def store_output(dev, filename, stage, command):
    if not dev.connected:
        reconnect = reconnect_dev(dev, 2)
        if not reconnect:
            logging.info("{}:  Connection Failed to {}\n".format(datetime.now(), dev.hostname))
            rpc_query = 'dev.rpc.cli("{}", format = "text")'.format(command)
            logging.debug('Getting output for {}'.format(command))
            rpc_response = eval(rpc_query)
            if not type(rpc_response) == bool:
                fout = open(filename, 'a')
                fout.write('===========================================================\n')
                fout.write("{}: {}\n".format(stage.upper(), command))
                fout.write('-----------------------------------------------------------\n')
                fout.write('{}\n'.format(datetime.now()))
                fout.write(rpc_response.text)
                fout.write('===========================================================\n')
                fout.close()
            else:
                fout = open(filename, 'a')
                fout.write('===========================================================\n')
                fout.write("{}: {}\n".format(stage.upper(), command))
                fout.write('-----------------------------------------------------------\n')
                fout.write('{}\n'.format(datetime.now()))
                fout.write('No Output\n')
                fout.write('===========================================================\n')
                fout.close()

# Get software information from both REs
# Returns a dict with RE as key and version as value
def get_sw_info(dev):
    sw_info = {}
    version_match = False
    dual_re = False

    if not dev.connected:
        reconnect = reconnect_dev(dev, 2)
        if not reconnect:
            logging.info("Connection Failed to {}\n".format(dev.hostname))
            return sw_info, version_match
    get_sw_info = dev.rpc.cli('show version invoke-on all-routing-engines', format='xml') 
    for RE in get_sw_info.findall('multi-routing-engine-item'):
        if RE.find('software-information/junos-version') is not None:
            sw_info[RE.find('re-name').text] = RE.find('software-information/junos-version').text
        else:
            for pkg in RE.findall('software-information/package-information'):
                if pkg.find('name').text == 'junos':
                    sw_info[RE.find('re-name').text] = re.search(r'\[.*\]', pkg.find('comment').text).group(0)[1:-1]
    if sw_info.has_key('re0') and sw_info.has_key('re1'):
        dual_re = True
        if sw_info['re0'] == sw_info['re1']:
            version_match = True
        elif sw_info.has_key('re0'):
            logging.info("The system does not have RE in slot 1")
        else:
            logging.info("The system does not have RE in slot 0")
    return sw_info, version_match, dual_re


# Run RSI and save the output locally on the router
# By default, the script will get the RSI brief. For a full RSI, call this function with brief=False
def save_data(dev, step, **options):
    from jnpr.junos.utils.fs import FS
    from jnpr.junos.utils.start_shell import StartShell
    if not dev.connected:
        reconnect = reconnect_dev(dev, 2)
        if not reconnect:
            logging.info("Connection Failed to {}\n".format(dev.hostname))
            return
    if options.has_key('script_name'):
        script_name = options['script_name']
    else:
        script_name = False
    if options.has_key('rsi'):
        rsi = True
        if options['rsi'] == 'brief':
            brief = True
        else:
            brief = False
    else:
        rsi = False
    if options.has_key('folder'):
        dst_dir = options['folder']
    else:
        dst_dir = '/var/tmp'
    if options.has_key('save_config'):
        save_config = options['save_config']
    else:
        save_config = False
    # Start Shell
    dev_shell = StartShell(dev)
    dev_shell.open()
    # Get RSI
    if rsi:
        logging.info('Running "request support information", this may take a while')
        if brief:
            rsi_cli = dev_shell.run(
                'cli -c "request support information brief | save {}/{}_rsi.txt"'.format(dst_dir, step))
        else:
            rsi_cli = dev_shell.run('cli -c "request support information | save {}/{}_rsi.txt"'.format(dst_dir, step))
    # Run OP Script
    if script_name:
        logging.info("Running op script: '{}' ... ".format(script_name))
        op_script = dev_shell.run('cli -c "op {} | save {}/{}_{}.txt"'.format(script_name, dst_dir, step, script_name))
    # Save Configuration
    if save_config:
        logging.info("Saving Configuration backup")
        cfg = dev_shell.run('cli -c "show configuration | save {}/{}_backup_config.txt"'.format(dst_dir, step))
    dev_shell.close()
    logging.info('Verifying stored files')
    dev_fs = FS(dev)
    tmp_list = dev_fs.ls(dst_dir)
    if rsi:
        if tmp_list['files'].has_key('{}_rsi.txt'.format(step)):
            logging.info("Compressing RSI")
            dev_fs.tgz('{}/{}_rsi.txt'.format(dst_dir, step),'{}/{}_Upgrade-MOP-support-information.tgz'.format(dst_dir, step))
            dev_fs.rm('{}/{}_rsi.txt'.format(dst_dir, step))
            if tmp_list['files'].has_key('{}_Upgrade-MOP-support-information.tgz'.format(step)):
                logging.info("RSI file saved in {}".format(dst_dir))
                rsi_complete = True
        else:
            logging.info("RSI collection did not complete in time\n")
    if save_config:
        if tmp_list['files'].has_key('{}_backup_config.txt'.format(step)):
            config_saved = True
            logging.info("Backup configuration saved to {}/{}_backup_config.txt".format(dst_dir, step))
        else:
            logging.info("Failed to save backup config")
    if script_name:
        if tmp_list['files'].has_key('{}_{}.txt'.format(step, script_name)):
            op_complete = True
            logging.info("OP {} script output saved in {}".format(script_name, dst_dir))
        else:
            logging.info("OP {} script did not complete Successfully".format(script_name))

# Request system snapshot
def save_snapshot(dev):
    sys_snap = False
    if not dev.connected:
        reconnect = reconnect_dev(dev, 2)
        if not reconnect:
            logging.info("Connection Failed to {}\n".format(dev.hostname))
            return sys_snap
    logging.info("Creating recovery snapshot")
    snap_rec = dev.rpc.cli('request system snapshot recovery routing-engine both')
    i = 0
    for item in snap_rec.findall('output'):
        if 'created successfully' in item.text:
            logging.info("Recovery Snapshot created successfully for re{}".format(i))
            sys_snap = True
            i += 1
        else:
            logging.info("Recovery Snapshot not successful")
            logging.info("Please Manually run the snapshot using the following command on master RE")
            logging.info("\t'request system snapshot recovery routing-engine both'")
    logging.info('Creating non recovery snapshot')
    snap_out = dev.rpc.cli('request system snapshot routing-engine both')
    i = 0
    for item in snap_out.findall('output'):
        if 'created successfully' in item.text:
            logging.info('Non Recovery snapshot created Successfully on re{}'.format(i))
            sys_snap = True
            i += 1
        else:
            logging.info('Non Recovery snapshot creation failed on re{}'.format(i))
            logging.info('Please manually create the snapshot using the following command')
            logging.info('request system snapshot routing-engine both')
            sys_snap = False
    return sys_snap


# Install SW and reboot RE (Should take about 15 Min's)
# Returns True if backup RE is back online after the upgrade
def install_and_reboot(dev, junos_path, backup_re):
    backup_re_upgraded = False
    backup_re_up = False
    if not dev.connected:
        reconnect = reconnect_dev(dev, 2)
        if not reconnect:
            logging.info("Connection Failed to {}\n".format(dev.hostname))
            return backup_re_up
    dev.timeout = 2400
    logging.info("Starting installation of software package on {}".format(backup_re))
    junos_file = junos_path.split('/')[-1]
    junos_ver = re.search(r'\d+\.\d.*\d', junos_file).group(0)
    backup_re_slot = backup_re[-1]
    # Installing software on backup RE
    local_junos_path = '{}:{}'.format(backup_re, junos_path)
    if backup_re_slot == '0':
        install_sw = dev.rpc.request_package_add(package_name=local_junos_path, re0=True, no_validate=True)
    elif backup_re_slot == '1':
        install_sw = dev.rpc.request_package_add(package_name=local_junos_path, re1=True, no_validate=True)
    logging.debug("Package Add RPC response: {}".format(install_sw))
    logging.info("Installation of software package is complete")
    logging.info("Attempting to Reboot {}....".format(backup_re))
    reboot_other_re = dev.rpc.request_reboot(other_routing_engine=True)
    # should add a check here to ensure that the reboot command took affect like its done on system reboot
    if reboot_other_re.text.__contains__('Rebooting'):
        logging.info('Reboot Started. This may take up to 15 minutes to complete')
        dev.close()
        time.sleep(480)
    else:
        logging.info('Attempt to reboot {} failed'.format(backup_re))
        logging.info('''
            Please reboot {} manually using the following command and Enter Yes after the RE comes back online to Continue
            If you are unable to perform this action, please Enter No to Exit the Script and manually take over the upgrade\n
            '''.format(backup_re))
        print "request system reboot other-routing-engine\n"
        move_on = user_prompt()
        reason = 'Unable to reload {}'.format(backup_re)
        if not move_on:
            return backup_re_upgraded, reason
    logging.info("Waiting for {} to come online...".format(backup_re))
    retry = 0
    while not backup_re_up and retry < 15:
        re_state, master = get_re_info(dev)
        backup_re_state = re_state[backup_re_slot]['status']
        logging.debug("RE status: {}".format(backup_re_state))
        logging.debug("RE Mastership: {}".format(re_state[backup_re_slot]['mastership-state']))
        if backup_re_state == 'OK':
            if re_state[backup_re_slot]['mastership-state'] == 'backup':
                backup_re_up = True
                logging.info("Backup RE, {}, is online and stable".format(backup_re))
                break
        retry += 1
        logging.info('Waiting for backup RE, {}, to stabilize'.format(backup_re))
        time.sleep(90)
    if not backup_re_up:
        logging.info("The backup RE, {}, has not come online after reboot in more than 30Min's".format(backup_re))
        logging.info("You can manually attempt to recover the backup RE now")
        logging.info("If you're able to recover the {}, please continue".format(backup_re))
        logging.info("Otherwise Stop\n")
        move_on = user_prompt()
        if not move_on:
            return backup_re_up
    # Verify that the RE is up with the latest Junos Version
    logging.info("Verifying the new SW version on backup RE, {}".format(backup_re))
    sw, match, dual_re = get_sw_info(dev)
    logging.debug("Current SW status: {}".format(sw))
    logging.debug("Target Version: {}".format(junos_ver))
    if sw[backup_re] == junos_ver:
        logging.info("Software update on {} complete".format(backup_re))
        backup_re_upgraded = True
    else:
        logging.info("Software update on {} Failed".format(backup_re))
    return backup_re_upgraded


#Upgrade BSYS
def upgrade_bsys(host, host_info):
    date = str(datetime.now())[:10]
    config_dir = '{}/configs'.format(os.path.dirname(os.path.realpath(__file__)))
    upgrade_complete = False

    logger = logging.getLogger()
    logging.getLogger("ncclient").setlevel(logging.ERROR)
    logging.getLogger("ncclient").setlevel(logging.ERROR)
    logger.handlers = []
    logger.setLevel(logging.NOTSET)
    formatter = logging.Formatter('{}: %(asctime)s - %(message)s'.format(host))
    #Log to file
    log_file = logging.FileHandler('{}/logs/{}_upgrade_{}_{}.log'.format(os.path.expanduser("~"), host, date, datetime.now().hour), 'a')
    log_file.setLevel(logging.DEBUG)
    log_file.setFormatter(formatter)
    logger.addHandler(log_file)
    #Log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logging.info("=" * 60)
    logging.info("Beginning Upgrade Procedure for {}".format(host))
    logging.info('''Upgrade logs will be saved in file: {}/logs/{}_upgrade_{}_{}.log'''.format(os.path.expanduser("~"), host, date, datetime.now().hour))
    logging.info('''Command logs will be saved in file: {}/logs/{}_upgrade_cmd_{}_{}.log'''.format(os.path.expanduser("~"), host, date, datetime.now().hour))
    logging.info('''PRE and POST upgrade configuration and op snapshot will be saved indirectory: /var/preserve of master RE\n''')
    time.sleep(4)

    cli_file = '{}/logs/{}_upgrade_cmd_{}_{}.log'.format(os.path.expanduser("~"), host, date, datetime.now().hour)

    logging.debug("Host Information ")
    logging.debug("-----------------")
    for key in host_info:
        if key == 'password':
            logging.debug("{}: ".format(key))
        else:
            logging.debug("{}: {}".format(key, host_info[key]))

    logging.info("Veryfing input data for {}: ".format(host))
    try:
        user = host_info['username']
    except:
        logging.info("Username not provided in the input file for: {}".format(host))
        reason = "Pre-upgrade: Username not provided"
        return upgrade_complete, reason
    try:
        passwd = host_info['password']
    except:
        logging.info("Password not provided in the input file for: {}".format(host))
        reason = "Pre-upgrade:Password not provided"
        return upgrade_complete, reason
    try:
        junos_path = host_info['junos_path']
    except:
        logging.info("Junos not provided in the input for {}".format(host))
        reason = "Pre-upgrade: Junos File not provided"
        return upgrade_complete, reason
    try:
        ftp_host = host_info['ftp_vars']['host'].strip()
        ftp_user = host_info['ftp_vars']['username'].strip()
        ftp_pwd = host_info['ftp_vars']['password']
    except:
        logging.info('FTP server information not provided in the input for {}'.format(host))
        reason = 'Pre-upgrade: FTP info not provided'
        return upgrade_complete, reason
    junos_file = junos_path.split('/')[-1]
    junos_ver = re.search(r'\d+\.\d.*\.\d', junos_file).group(0)
    logging.info("Input data verification complete\n")

    #Checking NETCONF
    logging.info("Verifying NETCONF Connectivity to: {}".format(host))
    dev = Device(host = host, user = user, password = passwd, gather_facts = False, port = 22)
    try:
        dev.open()
        dev.timeout = 3600
        logging.info("NETCONF Connectivity Verified\n")
    except:
        logging.info("Cannot Connect to {}\n".format(dev.hostname))
        reason = 'Pre-upgrade: Initial Login Failure'
        return upgrade_complete, reason

    post_upgrade = {}

    #Pre-upgrade check
    logging.info("Performing RE status Verification")
    pre_re, master = get_re_info(dev)  # Check that both RE are online, RE0 is master and RE1 is backup
    for key in pre_re:
        logging.info("RE{}: {}".format(key, pre_re[key]))
    store_output(dev, cli_file, 'pre-upgrade', 'show chassis routing-engine')
    logging.debug("RE Status: {}".format(pre_re))
    logging.debug("RE Mastership: {}".format(master))
    if pre_re['0']['status'] == pre_re['1']['status'] == 'OK':
        logging.info("Routing Engine status of both RE Verified\n")
    else:
        logging.info("RE Verification Failed, please check that both RE are online\n")
        reason = "Pre-upgrade: RE Verification Failed"
        return upgrade_complete, reason

    #SW check
    logging.info("Verifying software versions on the Routing Engines")
    pre_sw, version_match, dual_re = get_sw_info(dev)
    for key in pre_sw:
         logging.info("{}: {}".format(key, pre_sw[key]))
    if pre_sw['re0'].startswith('16.'):
         store_output(dev, cli_file, 'pre-upgrade', 'show version')
    else:
        store_output(dev, cli_file, 'pre-upgrade', 'show version invoke-on all-routing-engines')
    logging.debug("Pre Upgrade SW info: {}\n".format(pre_sw))
    logging.debug("version_match: {}\n".format(version_match))
    if not dual_re:
        logging.info("{} does not have two REs".format(host))
        reason = "{} is not an active dual RE system".format(host)
        dev.close()
        return upgrade_complete, reason
    if version_match:
        logging.info("SW versions on both RE match\n")
        if pre_sw[master['backup']] == pre_sw[master['master']] == junos_ver:
            logging.info("Both Routing Engines are already on ver {}".format(junos_ver))
            logging.info("Nothing to upgrade....\n")
            reason = "SW already on {}".format(junos_ver)
            upgrade_complete = True
            dev.close()
            return upgrade_complete, reason
    else:
        logging.info("SW Versions on both RE Do Not Match....\n")
        reason = "Pre-upgrade: SW Versions on both RE do Not match: Master={} , Backup={}".format(
            pre_sw[master['master']], pre_sw[master['backup']])
        dev.close()
        move_on = user_prompt()
        if not move_on:
            return upgrade_complete, reason

    # Save RSI/Config/Snapshot
    logging.info("Saving Pre upgrade data on the router")
    #save_data(dev, 'pre', rsi='brief', script_name='snapshot', folder='/var/preserve', save_config=True)
    save_data(dev, 'pre', rsi='brief', folder='/var/preserve', save_config=True)
    logging.info('Pre upgrade data gathering complete\n')


    # Upgrade Routing Engines that are not on the Target Version
    # If Master is on Target version, only upgrade the backup. RE switch-over is not performed in this case. Services are activated on the current master
    logging.info("Beginning RE upgrade process....")
    if pre_sw[master['master']] == junos_ver:
        logging.info("Master RE, {}, is the master and already upgraded to {}".format(master['master'], junos_ver))
        logging.info("Initiating Junos Installation on Backup RE {}".format(master['backup']))
        backup_re_up = install_and_reboot(dev, junos_path, master['backup'])
        if backup_re_up:
            logging.info("Backup RE, {}, is upgraded\n".format(master['backup']))
            # logging.info( "Verifying if HDD is mounted correctly\n")
        else:
            logging.info("Backup RE, {}, is still Not Online... Giving up\n".format(master['backup']))
            reason = "Upgrade: {} did Not come Online after Upgrade".format(master['backup'])
            dev.close()
            return upgrade_complete, reason
    # If Backup is on Target version, perform RE switch-over, upgrade the Master, perform another RE switch-over
    elif pre_sw[master['backup']] == junos_ver:
        logging.info('Backup RE, {} is already upgraded to {}'.format(master['backup'], junos_ver))
        logging.info('The Script will upgrade the current master only')
        # perform Mastership switch-over
        logging.debug("Pre Switch-over Status: {} ".format(master))
        logging.info("Attempting RE Switch-over")
        re_switchover, post_switch_master = do_re_switchover(dev, master)
        logging.debug("Post Switchover Status: {}".format(post_switch_master))
        if not re_switchover:
            logging.info("RE Switchover Not Successful...\n")
            reason = "Upgrade: First RE Switchover Not Successful"
            dev.close()
            move_on = user_prompt()
            if not move_on:
                return upgrade_complete, reason
        else:
            logging.info("RE Switchover Successful\n")

        # Upgrade the new Backup RE
        logging.info("Installing Junos on the previous Master")
        backup_re_up = install_and_reboot(dev, junos_path, post_switch_master['backup'])
        if backup_re_up:
            logging.info("Backup RE is Upgraded\n")
            # logging.info( "Verifying if HDD is mounted correctly\n")
        else:
            logging.info("Backup RE did not Upgrade.... Giving up\n")
            reason = "Upgrade: {} did not Upgrade".format(post_switch_master['backup'])
            return upgrade_complete, reason

        # Do another RE switchover
        logging.info("Attempting RE Switchover")
        logging.debug("Pre Switchover Status: {}".format(post_switch_master))
        re_switchover, post_switch2_master = do_re_switchover(dev, post_switch_master)
        logging.debug("Post Switchover Status: {}".format(post_switch2_master))
        if not re_switchover:
            logging.info("RE Switchover Not Successful...\n")
            reason = "Upgrade: Second RE Switchover Not Successful"
            dev.close()
            move_on = user_prompt()
            if not move_on:
                return upgrade_complete, reason
        else:
            logging.info("RE Switchover Successful\n")
    # If neither the Master or Backup are on the Target Version, upgrade both RE
    # First upgrade the backup, switchover, upgrade master, switchover
    else:
        # Install Junos on both routing-engines
        logging.info("Initiating Junos Installation on Backup RE {}".format(master['backup']))
        backup_re_up = install_and_reboot(dev, junos_path, master['backup'])
        if backup_re_up:
            logging.info("Backup RE, {}, is upgraded\n".format(master['backup']))
            # logging.info( "Verifying if HDD is mounted correctly\n")
        else:
            logging.info("Backup RE, {}, is still Not Online... Giving up\n".format(master['backup']))
            reason = "Upgrade: {} did Not come Online after Upgrade".format(master['backup'])
            dev.close()
            return upgrade_complete, reason

        # perform Mastership switchover
        logging.debug("Pre Switchover Status: {} ".format(master))
        logging.info("Attempting RE Switchover")
        re_switchover, post_switch_master = do_re_switchover(dev, master)
        logging.debug("Post Switchover Status: {}".format(post_switch_master))
        if not re_switchover:
            logging.info("RE Switchover Not Successful...\n")
            reason = "Upgrade: First RE Switchover Not Successful"
            dev.close()
            move_on = user_prompt()
            if not move_on:
                return upgrade_complete, reason
        else:
            logging.info("RE Switchover Successful\n")

        # Upgrade the new Backup RE
        logging.info("Installing Junos on the previous Master, {}".format(post_switch_master['backup']))
        backup_re_up = install_and_reboot(dev, junos_path, post_switch_master['backup'])
        if backup_re_up:
            logging.info("Backup RE, {}, is upgraded\n".format(post_switch_master['backup']))
            # logging.info( "Verifying if HDD is mounted correctly\n")
        else:
            logging.info("Backup RE, {}, did not Upgrade....Giving up\n".format(post_switch_master['backup']))
            reason = "Upgrade: {} did not Upgrade Properly".format(post_switch_master['backup'])
            return upgrade_complete, reason

        # Do another RE switchover
        logging.info("Attempting RE Switchover")
        logging.debug("Pre Switchover Status: {}\n".format(post_switch_master))
        re_switchover, post_switch2_master = do_re_switchover(dev, post_switch_master)
        logging.debug("Post Switchover Status: {}\n".format(post_switch2_master))
        if not re_switchover:
            logging.info("RE Switchover Not Successful...\n")
            reason = "Upgrade: Second RE Switchover Not Successful"
            dev.close()
            move_on = user_prompt()
            if not move_on:
                return upgrade_complete, reason
        else:
            logging.info("RE Switchover Successful\n")

    # Get post upgrade SW Version
    logging.debug("Getting SW versions on Both RE\n")
    post_sw, version_match, dual_re = get_sw_info(dev)
    for key in post_sw:
        logging.info("{}: {}".format(key, post_sw[key]))
    logging.debug("SW versions: {}\n".format(post_sw))




    return upgrade_complete, reason

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host_info", type=argparse.FileType("r"),help="YAML based file containing variables.")
    # input.add_argument('--y', action='store_true',help="Default option is to stop the process if any upgrade fails. Use this option to continue to the next router")
    PID = os.getpid()
    date = str(datetime.now())[:10]
    try:
        term_type = os.environ['TERM']
    except:
        term_type = 'unknown'
        print "Unable to determine terminal type\n"
    if term_type != 'screen':
        print "\n\t\tWARNING!!!"
        print "You are not running the upgrade script in a UNIX screen"
        print "Running the script in a screen will help avoid issues resulting from VPN Disconnects"
        print "Screen can be started by running:\n \t'screen -S <name>' on your UNIX prompt"
        move_on = user_prompt()
        if not move_on:
            print "Exiting...\n"
            raise SystemExit(1)
    summary = {}
    args = parser.parse_args()
    host_file = args.host_info
    try:
        host_vars = yaml.load(host_file)
    except:
        print "\nUnable to load the input file. Please check syntax and Retry!!\n"
        print "Exiting...\n"
        raise SystemExit(1)
    # Copy the global variables in the input file to all routers
    for item in host_vars:
        for seq in range(len(host_vars['hosts'])):
            for host in host_vars['hosts'][seq]:
                if item != 'hosts':
                    if not host_vars['hosts'][seq][host].has_key(item):
                        host_vars['hosts'][seq][host][item] = host_vars[item]

    # Create logs and summary directory in home directory if it does not exits
    try:
        os.stat('{}/logs'.format(os.path.expanduser("~")))
    except:
        print "{}/logs does not exist....Creating..\n".format(os.path.expanduser("~"))
        os.mkdir('{}/logs'.format(os.path.expanduser("~")))
    try:
        os.stat('{}/summary'.format(os.path.expanduser("~")))
    except:
        print "{}/summary does not exist....Creating..\n".format(os.path.expanduser("~"))
        os.mkdir('{}/summary'.format(os.path.expanduser("~")))

    # Open the summary file
    summary_file = open('{}/summary/{}_junos_upgrade_report_{}.csv'.format(os.path.expanduser("~"), host_file.name.split('/')[-1], date), 'a')
    summary_file.write('Host, Status, Comments, Start Time, End Time\n')
    for entry in range(len(host_vars['hosts'])):
        for host in host_vars['hosts'][entry]:
            if host_vars['hosts'][entry][host]['role'] == 'BSYS':
                try:
                    start_time = str(datetime.now().time())[:8]
                    if datetime.now().hour >= 0 and datetime.now().hour <= 6:  # for testing only
                        print "Current time: {}".format(start_time)
                        print "Starting an upgrade at this time may result in\n the upgrade completion after the Safe time"
                        print "The script will not attempt the upgrade for {} due to time constraints".format(host)
                        print "Please make sure the pre-upgrade steps are reverted"
                        print "Exiting...\n"
                        end_time = str(datetime.now().time())[:8]
                        upgrade_success = False
                        reason = "Pre-upgrade: Outside MW"
                    else:
                        print("Current Time {} is within the MW".format(start_time))
                        print(host)
                        print(type(host))
                        print(host_vars['hosts'][entry][host])
                        print(type(host_vars['hosts'][entry][host]))
                        upgrade_success, reason = upgrade_bsys(host, host_vars['hosts'][entry][host])
                        end_time = str(datetime.now().time())[ :8]
                except KeyboardInterrupt:
                    logging.info("User Interrupted the script")
                    logging.info("Upgrade for {} was Interrupted by User".format(host))
                    end_time = str(datetime.now().time())[:8]
                    upgrade_success = False
                    reason = "User Interrupted"
            summary[host] = {}
            summary[host]['start'] = start_time
            summary[host]['end'] = end_time
            if not upgrade_success:
                summary[host]['status'] = 'Failed'
                summary[host]['reason'] = reason
                logging.info("Upgrade did not complete on {} - reason: {} \n".format(host, reason))
                summary_file.write("{},{},{},{},{}\n".format(host, summary[host]['status'], summary[host]['reason'], summary[host]['start'], summary[host]['end']))
                failure_msg(reason)
                time.sleep(10)
                if entry + 1 < len(host_vars['hosts']):
                    logging.info("Do you want to continue to the NEXT Router? ")
                    proceed_on_failure = user_prompt()
                    if not proceed_on_failure:
                        logging.info("Script will STOP and NOT CONTINUE to the next host\n")
                        raise SystemExit(1)
            else:
                logging.info("Upgrade for {} Successful: {}\n".format(host, reason))
                logging.info("=" * 80)
                summary[host]['status'] = 'Success'
                summary[host]['reason'] = reason
                summary_file.write("{},{},{},{},{}\n".format(host, summary[host]['status'], summary[host]['reason'], summary[host]['start'], summary[host]['end']))
    summary_file.close()


if __name__ == '__main__':
    main()

