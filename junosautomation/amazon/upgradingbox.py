import time
from pprint import pprint
import sys

if sys.version_info < (3, 4):
    raise RuntimeError("This package requires Python 3.4+")
import warnings
import jnpr.junos
from jnpr.junos import Device
from jnpr.junos.utils.sw import SW
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import ConnectAuthError
from jnpr.junos.exception import ConnectTimeoutError
import re
from lxml import etree
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import LockError
from datetime import datetime
from jnpr.junos.utils.start_shell import StartShell
import argparse
import yaml
import subprocess
import multiprocessing
from pathlib import Path

if not sys.warnoptions:
    warnings.simplefilter("ignore")

script_version = "v1.1.0"

junos_image_location_map = {}
hw_compatibility_map = {}
junos_image_name_format_map = {}
junos_image_name_format_selector = {}
split_copy_path = ""
baseline_groups = []
credentials_list = []
fqdn_regex = ""
fqdn_suffix = ""


def set_personality(config):
    if Path(config).is_file():
        with open(config, 'r') as yaml_file:
            config = yaml.load(yaml_file)
            global junos_image_location_map
            global hw_compatibility_map
            global junos_image_name_format_map
            global junos_image_name_format_selector
            global split_copy_path
            global baseline_groups
            global credentials_list
            global fqdn_regex
            global fqdn_suffix
            junos_image_name_format_selector = config['junos_image_name_format_selector']
            junos_image_name_format_map = config['junos_image_name_format_map']
            junos_image_location_map = config['junos_image_location_map']
            hw_compatibility_map = config['hw_compatibility_map']
            split_copy_path = config['split_copy_path']
            baseline_groups = config['baseline_groups']
            credentials_list = config['credentials_list']
            fqdn_regex = config['fqdn_regex']
            fqdn_suffix = config['fqdn_suffix']

    else:
        print("Config file for this script ", args.config, " is not available. Script will now exit")
        sys.exit(1)


def load_baseline_config(router, router_name, current_re_only):
    shellSession = StartShell(router)
    shellSession.open()
    with open('baseline_from_router.set', 'w') as base_config:
        for group in baseline_groups:
            shell_output = shellSession.run('cli -c "show configuration groups ' + group + '| display set| no-more"')
            config = (shell_output[1].split('\n'))[
                     1:-1]  # Use second element of shell_ouput list. Remove first and last line. First line is the command executed and last line is cli prompt.
            if len(config) > 0:
                for config_command in config:
                    base_config.write(config_command)
                base_config.write('set apply-groups ' + group + '\n')
        base_config.write(' set system services netconf ssh' + '\n')
    shellSession.close()

    router.open()
    facts = dict((router.facts))
    syncrhonize = False

    if not current_re_only:
        if 're0' in list(facts['current_re']):

            if facts['RE1']:
                if (str(facts['RE1']['status']) == 'OK'):
                    syncrhonize = True

        elif 're1' in list(facts['current_re']):
            if facts['RE0']:
                if (str(facts['RE0']['status']) == 'OK'):
                    syncrhonize = True

    with Config(router) as cu:
        try:
            cu.load('', overwrite=True, format="text", ignore_warning=True)
            cu.load(path='baseline_from_router.set', format="set", ignore_warning=True)
            cu.commit(force_sync=syncrhonize, timeout=360)
            print ("Applied baseline config on ", router_name, "\n")
            router.close()
            return 0
        except Exception as e:
            print(str(e))
            print ("\n\nFailed to load basedline config to ", router_name, "\n\n")
            router.close()
            return 1


def custom_sleep(sleep_time, device_address):
    print ("\nSleeping for", sleep_time, "seconds before checking status of", device_address)
    t = 0
    while (t < sleep_time):
        # print(t+1, end=" ", flush=True)
        time.sleep(1)
        t = t + 1


def wait_for_router_online(router, sleep_time, device_address):
    while (1):
        custom_sleep(sleep_time, device_address)
        try:
            router.open()
        except:
            print("Couldn't connect to", device_address, sleep_time,
                  "seconds after reboot. Script will sleep again to retry later.")
            print(
            "You may have to stop the script with ctrl+c and check router manually if the script has been waiting too long for",
            device_address, "to come online.")
        if router.connected:
            router.close()
            return 0


def do_junos_upgrade(router, cleanfsflag, device_address, device_username, device_password, junos_version_for_upgrade,
                     current_re_only, copy_only):
    router.open()
    facts = dict((router.facts))
    router.close()
    current_re_model = None

    if str(facts['version']) == str(junos_version_for_upgrade):
        print(device_address, "already is running on junos version", junos_version_for_upgrade)
        return 0

    if 're0' in list(facts['current_re']):
        if dict(facts['RE0'])['model']:
            current_re_model = dict(facts['RE0'])['model']
        else:
            print("Script could not fetch Model of RE0 from", device_address,
                  "which is the current RE. Script will not upgrade", device_address, "\n")
            return 1
        if not current_re_only:
            if facts['RE1']:
                if (str(facts['RE1']['model']) != str(current_re_model)):
                    current_re_only = True
                    print("Script is logged in to RE0 of", device_address,
                          "Either the script could not fetch the RE type of RE1 or the RE type of RE0 does not match RE1. Script will only upgrade RE0 on",
                          device_address, "\n")
                if (not current_re_only) and (str(facts['RE1']['status']) != 'OK'):
                    current_re_only = True
                    print("Script is logged in to RE0 of", device_address,
                          "Status of RE1 is not \'OK\'. Script will only upgrade RE0 on", device_address, "\n")
                if (not current_re_only) and facts['version_RE1']:
                    if str(facts['version_RE1']) == junos_version_for_upgrade:
                        current_re_only = True
                        print("Script is logged in to RE0 of", device_address, "RE1 is already running junos version",
                              junos_version_for_upgrade, "Script will only upgrade RE0 on", device_address, "\n")
                else:
                    current_re_only = True
                    print("Script is logged in to RE0 of", device_address,
                          "Script could not fetch version info from RE1. Script will only upgrade RE0 on",
                          device_address, "\n")

            else:
                current_re_only = True
                print("Script is logged in to RE0 of", device_address,
                      "Script could not fetch RE1 info. Script will only upgrade RE0 on", device_address, "\n")

    elif 're1' in list(facts['current_re']):
        if dict(facts['RE1'])['model']:
            current_re_model = dict(facts['RE1'])['model']
        else:
            print("Script could not fetch Model of RE1 from", device_address,
                  "which is the current RE. Script will not upgrade", device_address, "\n")
            return 1
        if not current_re_only:
            if facts['RE0']:
                if (str(facts['RE0']['model']) != str(current_re_model)):
                    current_re_only = True
                    print("Script is logged in to RE1 of", device_address,
                          "Either the script could not fetch the RE type of RE0 or the RE type of RE0 does not match RE1. Script will only upgrade RE1 on",
                          device_address, "\n")
                if (not current_re_only) and (str(facts['RE0']['status']) != 'OK'):
                    current_re_only = True
                    print("Script is logged in to RE1 of", device_address,
                          "Status of RE0 is not \'OK\'. Script will only upgrade RE1 on", device_address, "\n")
                if (not current_re_only) and facts['version_RE0']:
                    if str(facts['version_RE0']) == junos_version_for_upgrade:
                        current_re_only = True
                        print("Script is logged in to RE1 of", device_address, "RE0 is already running junos version",
                              junos_version_for_upgrade, "Script will only upgrade RE1 on", device_address, "\n")
                else:
                    if (not current_re_only):
                        current_re_only = True
                        print("Script is logged in to RE1 of", device_address,
                              "Script could not fetch version info from RE0. Script will only upgrade RE1 on",
                              device_address, "\n")

            else:
                current_re_only = True
                print("Script is logged in to RE1 of", device_address,
                      "Script could not fetch RE0 info. Script will only upgrade RE1 on", device_address, "\n")

    else:
        print ("Script could not identify current RE Model. Script will not upgrade", device_address, "\n")
        return 1

    if not current_re_model:
        print ("Script could not identify current RE Model. Script will not upgrade", device_address, "\n")
        return 1

    version_year = re.search('^(\d*)\..*$', junos_version_for_upgrade).group(1)
    major_version = re.search('^(\d*\.\d).*$', junos_version_for_upgrade).group(1)
    junos_name_format_type = None
    junos_name_format = None
    junos_image_name = None
    junos_image_location_format = None
    junos_image_path = None
    found_valid_image = False

    for format_map_key in junos_image_name_format_selector.keys():
        if (junos_image_name_format_selector[format_map_key]['from'] <= int(version_year) <=
                junos_image_name_format_selector[format_map_key]['to']):
            junos_name_format_type = format_map_key

    if junos_name_format_type is None:
        print("Couldn't fetch Junos name format type. Script will not upgrade", device_address)
        return 1

    put_version_in_format = re.compile('^(.*)(VERSION_NUMBER)(.*)$')
    put_version_in_image_location = re.compile('^(.*)(MAJOR_VERSION_NUMBER)(.*)(VERSION_NUMBER)(.*)$')
    daily_image_format = re.compile('^(\d*\.\d)I\-(\d{8})\.(\d)\.(\d{4})$')
    junos_version_in_directory_path = junos_version_for_upgrade

    if daily_image_format.match(junos_version_for_upgrade):  # for daily image
        junos_version_in_directory_path = daily_image_format.search(junos_version_for_upgrade).group(
            2) + daily_image_format.search(junos_version_for_upgrade).group(4) + '.' + daily_image_format.search(
            junos_version_for_upgrade).group(3)

    print("Model of current RE in", device_address, "is:", current_re_model)

    try:
        junos_name_format = str(junos_image_name_format_map[junos_name_format_type][current_re_model])
        junos_image_name = put_version_in_format.sub(r"\g<1>" + str(junos_version_for_upgrade) + r"\g<3>",
                                                     junos_name_format)
        junos_image_location_format = junos_image_location_map[current_re_model]
        try:
            for image_path in list(junos_image_location_format):
                junos_image_path = put_version_in_image_location.sub(
                    r"\g<1>" + str(major_version) + r"\g<3>" + str(junos_version_in_directory_path) + r"\g<5>",
                    image_path) + str(junos_image_name)
                if (Path(junos_image_path).is_file()):
                    print ("Junos image for upgrading current RE in", device_address, "is at: ", junos_image_path)
                    found_valid_image = True
                    break
        except:
            print("Error in fetching image file location for,", device_address,
                  "from image location format configuration. Please check if correct image location format is available in script configuration file for RE Type: ",
                  current_re_model)
            return 1
    except:
        print("Error in fetching image name for", device_address,
              "based on image name format configuration. Please check if correct image name format is available in script configuration file for RE Type: ",
              current_re_model)
        return 1

    if not found_valid_image or not junos_image_path:
        print(
        "Error in finding suitable junos image to upgrade", device_address, "Script will not upgrade", device_address)
        return 1

    router.open()
    sw = SW(router)
    file_copy_status = 1
    is_vmhost_image = False
    local_checksum_string = None
    remote_checksum_string = None
    checksum_matches = False

    if ('vmhost' in junos_image_path):
        is_vmhost_image = True

    print ("Checking whether the device", device_address, "already have the junos image file", junos_image_name,
           "in /var/tmp/ directory")

    if Path(junos_image_path + '.md5').is_file():
        remote_checksum_string = sw.remote_checksum('/var/tmp/' + junos_image_name, algorithm='md5')
        if remote_checksum_string:
            with open(junos_image_path + '.md5') as checksum_data:
                local_checksum_string = str(checksum_data.readline()).split()[0].rstrip()
            if remote_checksum_string == local_checksum_string:
                checksum_matches = True
    elif Path(junos_image_path + '.sha1').is_file():
        remote_checksum_string = sw.remote_checksum('/var/tmp/' + junos_image_name, algorithm='sha1')
        if remote_checksum_string:
            with open(junos_image_path + '.sha1') as checksum_data:
                local_checksum_string = str(checksum_data.readline()).split()[0].rstrip()
            if remote_checksum_string == local_checksum_string:
                checksum_matches = True
    elif Path(junos_image_path + '.sha256').is_file():
        remote_checksum_string = sw.remote_checksum('/var/tmp/' + junos_image_name, algorithm='sha256')
        if remote_checksum_string:
            with open(junos_image_path + '.sha256') as checksum_data:
                local_checksum_string = str(checksum_data.readline()).split()[0].rstrip()
            if remote_checksum_string == local_checksum_string:
                checksum_matches = True
    else:
        remote_checksum_string = sw.remote_checksum('/var/tmp/' + junos_image_name)
        if remote_checksum_string:
            local_checksum_string = sw.local_checksum(junos_image_path)
            if remote_checksum_string == local_checksum_string:
                checksum_matches = True

    if checksum_matches:
        print (
        "Device already have the junos image file", junos_image_name, "in /var/tmp/ directory of", device_address,
        "Script will use this file to perform the upgrade.")
        file_copy_status = 0
    else:
        print ("The device", device_address, "do not have the junos image file", junos_image_name,
               "in /var/tmp/ directory. Script will copy the required junos image.")
        if Path(str(split_copy_path)).is_file():
            print ("Script will now attempt to use splitcopy.py script to copy", junos_image_path, "to", device_address)
            print("running command:", str(split_copy_path), junos_image_path,
                  device_username + "@" + device_address + ":/var/tmp/", "--pwd", device_password)

            try:
                file_copy_status = subprocess.call(
                    [str(split_copy_path), junos_image_path, device_username + "@" + device_address + ":/var/tmp/",
                     "--pwd", device_password], stdout=sys.stdout, stderr=subprocess.DEVNULL, timeout=900)
            except Exception as e:
                file_copy_status = 1
                print("Attempt to copy the image to", device_address, "using splitcopy utility failed.")
                print(str(e))

            if file_copy_status != 0:
                print ("splitcopy couldn't copy the image to", device_address,
                       "\nScript will use junos pyEZ jnpr.junos.utls.sw.put() to copy image to device. This process will be slower.")
                try:
                    sw.put(junos_image_path, progress=True)
                    file_copy_status = 0
                except Exception as e:
                    print(str(e))
        else:
            print (
                "Scipt couldnt locate splitcopy utility. Script will use junos pyEZ jnpr.junos.utls.sw.put() to copy image to device. This process will be slower.")
            try:
                sw.put(junos_image_path, progress=True)
                file_copy_status = 0
            except Exception as e:
                print(str(e))

    if file_copy_status != 0:
        print("Script could not copy the required junos image file to current RE of", device_address,
              "Upgrade will not be performed on", device_address)
        router.close()
        return 1

    if copy_only:
        print("Script successfully copied", junos_image_name, "to /var/tmp/ directory of", device_address)
        router.close()
        return 0

    try:
        installation_status = sw.install(package="/var/tmp/" + junos_image_name, no_copy=True, progress=True,
                                         vmhost=is_vmhost_image, cleanfs=cleanfsflag, all_re=not (current_re_only))

        if installation_status:
            print ("Rebooting", device_address, "after junos upgrade")
            try:
                sw.reboot(all_re=not (current_re_only), vmhost=is_vmhost_image)
            except:
                pass  ## Pyez throws an exception after rebooting vmhost devices. This can be removed after it is fixed.
            router.close()
            wait_for_router_online(router, 300, device_address)
            router.open()
            if str(dict(router.facts)['version']) == str(junos_version_for_upgrade):
                print(device_address, "was successfully upgraded to", junos_version_for_upgrade)
                return 0
            else:
                print("Script attempted upgrading", device_address, "to", junos_version_for_upgrade,
                      "and rebooted the device. But current version is still not the target version.")
                return 1
        else:
            print("Script could not complete installation of new junos image in ", device_address)
            router.close()
            return 1

    except Exception as e:
        print("Script could not complete installation of new junos image in ", device_address)
        print(str(e))
        router.close()
        return 1


def upgrade_device(device_name, device_username, device_password, load_baseline, cleanfs_flag, device_version,
                   current_re_only, copy_only):
    router_name = ''
    router_name_is_ip = False
    router = None
    device_uname = ""
    device_passwd = ""

    if re.match(fqdn_regex, device_name):
        router_name = str(re.search(fqdn_regex, device_name).group(1))
    elif re.match(
            '^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$',
            device_name):
        router_name = device_name
        router_name_is_ip = True
    else:
        router_name = device_name

    if device_password and device_username:
        device_uname = device_username
        device_passwd = device_password
        if router_name_is_ip:
            router = Device(host=router_name, user=device_username, password=device_password)
        else:
            router = Device(host=router_name + fqdn_suffix, user=device_username, password=device_password)
        try:
            router.open()
        except ConnectAuthError:
            print (
                "Connection attempt to router failed because of authentication error. Please provide valid credentials.\n")
            sys.exit(1)
        except ConnectTimeoutError:
            print (
                "Connection attempt to router was timed out. Please make sure if the device is powered on and reachable from this server and whether netconf service via ssh is enabled on the device.\n")
            sys.exit(1)
        except ConnectError as err:
            print ("Cannot connect to device: {0}".format(err), "\n\nScript will now exit.")
            sys.exit(1)
    else:
        credentials_list_length = len(credentials_list)
        current_list_item = 1
        for credential in credentials_list:
            if router_name_is_ip:
                router = Device(host=router_name, user=credential['username'], password=credential['password'])
            else:
                router = Device(host=router_name + fqdn_suffix, user=credential['username'],
                                password=credential['password'])
            try:
                router.open()
                device_uname = credential['username']
                device_passwd = credential['password']
                break
            except ConnectAuthError:
                if credentials_list_length == current_list_item:
                    print(
                        "Could not connect to device using any credential mentioned in script config file. Script will now exit.\n")
                    sys.exit(1)
                else:
                    current_list_item += 1
                    pass
            except ConnectTimeoutError:
                print (
                    "Connection attempt to router was timed out. Please make sure if the device is powered on and reachable from this server and whether netconf service via ssh is enabled on the device.\n")
                sys.exit(1)
            except ConnectError as err:
                print ("Cannot connect to device: {0}".format(err), "\n\nScript will now exit.")
                sys.exit(1)

    if router.connected:
        router.close()

    if load_baseline:
        if load_baseline_config(router, router_name, current_re_only) != 0:
            print("\nFailed to commit the baseline config on ", router_name, "Script will not attempt upgrade on",
                  router_name, "\n")
            sys.exit(1)

    upgrade_status = None
    if router_name_is_ip:
        upgrade_status = do_junos_upgrade(router, cleanfs_flag, router_name, device_uname, device_passwd,
                                          device_version, current_re_only, copy_only)
    else:
        upgrade_status = do_junos_upgrade(router, cleanfs_flag, router_name + fqdn_suffix, device_uname, device_passwd,
                                          device_version, current_re_only, copy_only)

    if not (upgrade_status is None):
        if upgrade_status != 0:
            print("\n")
            print("Activity on", router_name, "was not completed.")
    sys.exit(0)


if __name__ == "__main__":
    execution_start_time = datetime.now()
    arg_parse = argparse.ArgumentParser()
    arg_parse.add_argument('--ver', action='append', dest='version_list', default=[],
                           help='Mandatory: Junos version to upgrade to', type=str)
    arg_parse.add_argument('--device', action='append', dest='device_list', default=[],
                           help='Mandatory: Name of device on which the config has to be loaded', type=str)
    arg_parse.add_argument('--loadbaseline', action='store_true',
                           help='Optional: if specified, script will extract baseline config and load it on device before upgrade')
    arg_parse.add_argument('--username', help='Optional: Username to login to device', type=str)
    arg_parse.add_argument('--password', help='Optional: Password to login to device', type=str)
    arg_parse.add_argument('--version', action='version', version='%(prog)s ' + script_version)
    arg_parse.add_argument('--config', default=str(sys.path[0]) + '/upgrade-device.yaml',
                           help='Optional: Config file (yaml) for this script', type=str)
    arg_parse.add_argument('--cleanfs', action='store_true',
                           help='Optional: if specified, script will perform storage cleanup during junos upgrade')
    arg_parse.add_argument('--copyonly', action='store_true',
                           help='Optional: if specified, script will only copy the image file to the device and will not perform the upgrade')
    arg_parse.add_argument('--currentre', action='store_true',
                           help='Optional: if specified, script will perform upgrade only on routing-engine to which script logs in')
    args = arg_parse.parse_args()

    if len(args.version_list) == 0:
        print("Manadatory argument --ver is missing. Use --help option to see script arguments. Script will now exit.")
        sys.exit(1)
    if len(args.device_list) == 0:
        print(
            "Manadatory argument --device is missing. Use --help option to see script arguments. Script will now exit.")
        sys.exit(1)

    if len(args.version_list) > 1:
        if len(args.version_list) != len(args.device_list):
            print("No. of version arguments(", len(args.version_list) + 1, ") not equal to no. of device arguments(",
                  len(args.version_list) + 1, "). Script will now exit.")
            sys.exit(1)

    set_personality(args.config)

    upgrade_process_list = []

    for i in range(len(args.device_list)):
        if len(args.version_list) > 1:
            device_upgrade_process = multiprocessing.Process(target=upgrade_device,
                                                             args=[args.device_list[i], args.username, args.password,
                                                                   args.loadbaseline, args.cleanfs,
                                                                   args.version_list[i], args.currentre, args.copyonly])
            upgrade_process_list.append(device_upgrade_process)
        else:
            device_upgrade_process = multiprocessing.Process(target=upgrade_device,
                                                             args=[args.device_list[i], args.username, args.password,
                                                                   args.loadbaseline, args.cleanfs,
                                                                   args.version_list[0], args.currentre, args.copyonly])
            upgrade_process_list.append(device_upgrade_process)

    for upgrade_process in upgrade_process_list:
        upgrade_process.start()

    for upgrade_process in upgrade_process_list:
        upgrade_process.join()

    print ("Script attempted upgrade/copy on all specified devices. Script will now Exit.")
    execution_end_time = datetime.now()
    print("Script execution duration:", execution_end_time - execution_start_time)

    sys.exit(0)
