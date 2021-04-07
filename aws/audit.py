#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import sys
import logging
import argparse
import re
import collections
import paramiko
import os
import subprocess
import getpass
import time
from os.path import expanduser

home = expanduser("~")

TIME_APPENDIX = time.strftime("-%Y%m%d-%H%M%S")
QUERY_VC_DEVICE_FILE = "/apollo/env/DXDeploymentTools/audit/query.txt"
AUDIT_LOG_FILE = '{}/dx_audit{}.log'.format(str(home),TIME_APPENDIX)
OUTPUT_FILE = "{}/dx_output{}.txt".format(str(home),TIME_APPENDIX)

MAX_AUTH_FAIL = 5
auth_fail_count = 0
FAILED_LOGIN_DEVICE_CLIS = list()
AUTH_FAIL_GUIDE = """
When you see authentication failed. Please check the following two steps:
1, kinit to run before you run this script
"""

CLI_BLACKLIST = ["show route"]
REQUEST_WHITELIST = ["request system configuration rescue save",
                     "request system software delete jpuppet",
                     "request system software delete ruby",
                     "request system software delete chef",
                     "request system software delete junos-ez-stdlib",
                     ]

ACCEPT_DEVICE_LIFECYCLE_STATUS = ["MAINTENANCE", "OPERATIONAL"]

DEFAULT_HEAD_ROWS_NUM = 1
DEFAULT_WITHIN_LINE_DELIMITER = ","
DEFAULT_INTER_LINE_DELIMITER = "\n"
DEFAULT_INTEREST_COLUMNS = tuple([0])

# flag for different python version
IS_PYTHON_V2 = True
if sys.version_info[0] < 3:
    get_input = raw_input
else:
    get_input = input
    IS_PYTHON_V2 = False

#
logging.basicConfig(filename=AUDIT_LOG_FILE,
                    level=logging.DEBUG,
                    format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s")



def read_query_dx_devices_file(file):
    devices = set()
    with open(file, "r") as f:
        for line in f:
            wrong_status = True
            for status in ACCEPT_DEVICE_LIFECYCLE_STATUS:
                if status in line:
                    wrong_status = False
            if wrong_status:
                continue
            device = line.split(",")[0]
            devices.add(device)
    return devices


def max_len(items):
    """
    return of the max lenght of all the strings in a list
    :param items: list of string
    :return:
    """
    max_lenght = 0
    for item in items:
        cur_lenght = len(item)
        if cur_lenght > max_lenght:
            max_lenght = cur_lenght
    return max_lenght


def test_max_len():
    a_list = ["a", "ab"]
    assert max_len(a_list) == 2
    a_list = ["", "", ""]
    assert max_len(a_list) == 0
    return


def get_list_of_columns(stream,
                        head_rows_num=DEFAULT_HEAD_ROWS_NUM,
                        columns=DEFAULT_INTEREST_COLUMNS,
                        within_line_delimiter=DEFAULT_WITHIN_LINE_DELIMITER,
                        inter_line_delimiter=DEFAULT_INTER_LINE_DELIMITER):
    """
    get list of columns from stream
    :param stream:  the multi_line text
    :param head_rows_num:  head of row default is 1
    :param columns: default is column 0, 1st column
    :param within_line_delimiter:
    :param inter_line_delimiter:

    :return:
        the list of columns records
    """
    # result_l = list()
    result_s = set()  # use set to remove repeat item, otherwise use list as before
    result = result_s  # result_l
    max_column = max(columns)
    lines = stream.split(inter_line_delimiter)

    # check if less lines
    if len(lines) <= head_rows_num:
        logging.error("no valid content given")
        return result

    for line in lines[head_rows_num:]:  # skip read head lines
        words = line.split(within_line_delimiter)
        # check if items is less then required or empty item in this line, skip this line
        if len(words) < max_column or max_len(words) < 1:
            logging.debug("{} is over limit of {}".format(line, str(max_column)))
            continue
        if len(columns) == 1:
            item = words[columns[0]]
        else:  # multi columns use tuple to encapture multiple values in a record
            item = tuple([words[c] for c in columns])
        # result_l.append(item)
        result.add(item)

    # return remove_repeat_items_for_list_of_list(result)
    return sorted(list(result))


def get_username():
    username = getpass.getuser()
    indication = "username({}): ".format(username)
    user_input = get_input(indication)
    if len(user_input) > 1:
        username = user_input
    return username


def audit():
    parser = argparse.ArgumentParser(description='Audit by running show commands in devices')
    parser.add_argument('--command', help='file with command list, with each cmd in a line')
    parser.add_argument('--command_file', help='file with command list, with each cmd in a line')
    parser.add_argument('--device', help='give exact one device name')
    parser.add_argument('--device_reg', help='give device regular expression')
    parser.add_argument('--query_file', help='the file save query result, to give device list')
    parser.add_argument('--interface_csv', help='csv file with device and interfaces')
    parser.add_argument('--tt', help='give the ticket id, when you need to run command start with "request"')
    parser.add_argument('--output_file', help='give the outputname, defaut is "{}"'.format(OUTPUT_FILE))
    parser.add_argument('--query_all', help='give the outputname, defaut is "{}"'.format(OUTPUT_FILE))

    parser.add_argument('--pw', help=argparse.SUPPRESS)
    args = parser.parse_args()

    file = QUERY_VC_DEVICE_FILE
    if args.query_all:
        file = args.query_all

    # load query txt as valid device source
    dx_devices = read_query_dx_devices_file(file)

    def valid_device(device_name):
        if device_name in dx_devices:
            return True
        logging.error("{} is not valid device".format(device_name))
        return False

    def valid_cli(cli_name):
        result = True
        if cli_name in CLI_BLACKLIST:
            result = False
        if re.match("request", cli_name) and cli_name not in REQUEST_WHITELIST:
            result = False
        if not result:
            logging.error("{} is not valid cli".format(cli_name))
        return result

    # get device or device/interfaces info
    valid_input_flag = True
    devices = list()
    interfaces_of_device = collections.defaultdict(list)
    if args.device:
        device = args.device
        if valid_device(device):
            devices.append(device)
        else:
            valid_input_flag = False
    elif args.device_reg:
        patterm = args.device_reg
        for device in dx_devices:
            if patterm in device:
                devices.append(device)
                continue
            if re.match(patterm, device):
                #print(patterm)
                devices.append(device)
        device_str = "\n".join(devices)
        print("The Device List is: \n{}\n".format(device_str))

        if len(devices) < 1:
            valid_input_flag = False
    elif args.interface_csv:
        file = args.interface_csv
        file_text = ""
        logging.info("reading file: {}".format(file))
        with open(file, "r") as f:
            file_text = f.read()
        device_intf_peer = get_list_of_columns(file_text, columns=[0, 1])

        for device, interface in device_intf_peer:
            if not valid_device(device):
                continue
            interfaces_of_device[device].append(interface)

        if len(interfaces_of_device) < 1:
            valid_input_flag = False
    elif args.query_file:
        file = args.query_file
        logging.info("reading file: {}".format(file))
        with open(file, "r") as f:
            file_text = f.read()
        devices = get_list_of_columns(file_text)
        if len(devices) < 1:
            valid_input_flag = False
    else:
        valid_input_flag = False

    # get cli list
    clis = list()
    if args.command:
        clis.append(args.command)
    elif args.command_file:
        logging.info("reading file {}".format(args.command_file))
        with open(args.command_file, "r") as f:
            for line in f:
                right_command = False
                if re.match("show", line): # before using "show" not in line:  # only run show command
                    right_command = True
                elif re.match("request", line) and args.tt:
                    right_command = True

                if not right_command:
                    continue
                cli = line.strip()
                if not valid_cli(cli):
                    continue
                clis.append(cli)

    else:
        logging.info("no command given")
        valid_input_flag = False

    # get output file
    output_file = OUTPUT_FILE
    if args.output_file:
        output_file = output_file

    # print(clis)
    clis_str = "\n".join(clis)
    logging.info(clis_str)

    responses = list()
    #response = ""
    if not valid_input_flag:
        parser.print_help()
        return

    # print("input useranme/password now")
    if not args.pw:
        user = get_username()
        pw = getpass.getpass("password: ")
    else:
        user = getpass.getuser()
        pw = get_input()

    if args.tt:
        user = ".".join([user, "tt", args.tt])
    for device in interfaces_of_device:
        interfaces =interfaces_of_device[device]
        commands = list()
        for cli in clis:
            if "{interface}" not in cli:
                commands.append(cli)
                continue
            for interface in interfaces:
                command = cli.format(interface=interface)
                commands.append(command)
        response = run_clis(device, commands, user, pw)
        print(response)
        responses.append(response)
        if auth_fail_count > MAX_AUTH_FAIL:
            break

    # add device
    for device in devices:
        commands = clis
        response = run_clis(device, commands, user, pw)
        print(response)
        responses.append(response)
        if auth_fail_count > MAX_AUTH_FAIL:
            break

    for device,clis in FAILED_LOGIN_DEVICE_CLIS:
        commands = clis
        response = run_clis(device, commands, user, pw)
        print(response)
        responses.append(response)
        if auth_fail_count > MAX_AUTH_FAIL:
            break

    if auth_fail_count > MAX_AUTH_FAIL:
        print(AUTH_FAIL_GUIDE)

    all_response = "\n".join(responses)

    with open(output_file, "w") as wf:

        wf.write(all_response)
        logging.info("log wrote to file {}".format(output_file))
    return all_response

def get_paramiko_connection(device_name,user,pwd):
    logging.info("logging device: {}, with username {}".format(device_name,user))
    client = paramiko.SSHClient()
    client._policy = paramiko.WarningPolicy()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser("/apollo/env/DXDeploymentTools/audit/config")
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            ssh_config.parse(f)

    cfg = {'hostname':device_name,'username':user,'password':pwd}
    user_config = ssh_config.lookup(cfg['hostname'])
    port = 22
    for k in ('hostname','username','port'):
        if k in user_config:
            cfg[k] = user_config[k]

    if 'proxycommand' in user_config:
        subprocess_return = subprocess.check_output([os.environ['SHELL'], '-c', 'echo %s' % user_config['proxycommand']]).strip()
        if not IS_PYTHON_V2:
            subprocess_return = subprocess_return.decode()
        # print("subprocess_return is {}".format(subprocess_return))
        proxy = paramiko.ProxyCommand(subprocess_return)
        cfg['sock'] = proxy
    try:
        client.connect(**cfg)
        log_message =  "Connecting to %s \n" %device_name
        logging.info(log_message)
        return client
    except:
        log_error = "Could not connect to {}".format(device_name)
        logging.error(log_error)
    return False
def add_items_to_list(a_list, *args):
    item = tuple([arg for arg in args])
    a_list.append(item)
    return
def run_clis(device, clis, user, pw):
    """

    :param device:
    :param clis:
    :return: response from devices with clis
    """
    responses = list()
    response = ""

    global auth_fail_count

    clis_str = "\n".join(clis)
    log_info = "running following command(s) in {}: \n{}\n".format(device, clis_str)
    logging.info(log_info)

    conn = get_paramiko_connection(device,user,pw)
    if not conn:
        auth_fail_count += 1
        add_items_to_list(FAILED_LOGIN_DEVICE_CLIS, device, clis)
        print("Failed to connect to {}. Please check the username and password.".format(device))
        return ""
    for cli in clis:
        response = "\n{}@{}> {}\n".format(user, device, cli)

        stdin, stdout, stderr = conn.exec_command(cli)

        new_output = stdout.read()
        if not IS_PYTHON_V2:
            new_output = new_output.decode()
        response += new_output
        responses.append(response)
    conn.close()

    return "\n".join(responses)

if __name__ == "__main__":
    audit()

