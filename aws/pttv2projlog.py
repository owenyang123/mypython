#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import dxd_tools_dev.modules.pttv2_cli_module as cli_module
from dxd_tools_dev.modules.device import Credential
from dxd_tools_dev.modules import pttv2_gen_pwd
import argparse
import os
from datetime import datetime


DDB_RECORD_SEPERATION = "&"

HOME = os.getenv("HOME")
SLAX_LOG_SAVE_AT = f'{HOME}/pttv2'

class Color:
    BLUE = '\033[36m'
    RED = '\033[31m'
    ORANGE = '\033[33m'
    BLACK = '\033[30m'
    GREY = '\033[37m'
    WHITE = '\033[0m'


class TypeNotice:
    ALARM = "ALARM"
    ERROR = "ERROR"
    MESSAGE = "MESSAGE"


def notice(type, message):
    sayit = f"[{type}] {message}"
    print(sayit)


def convert_float_to_string(timestamp: float):
    return str(timestamp)

def convert_string_to_float(timestring: str):
    result = 0
    try:
        result = float(timestring)
    except:
        notice(TypeNotice.ERROR, f"{timestring} is not right timestring")
    return result

class TimeDiff:
    def __init__(self):
        self._before = datetime.now()
    def get_difference_in_seconds(self):
        self._after = datetime.now()
        diff = self._after - self._before
        if diff.seconds < 1:
            return 1
        return diff.seconds


class TimeObj:
    def __init__(self, time_string=None, formated_time=None):
        self._datetime = None
        if time_string is not None:
            self.get_time_from_timestring(time_string)
        elif formated_time is not None:
            self.get_time_from_slaxlog(formated_time)
        else:
            self.get_time_now()

    def get_time_now(self):
        self._datetime = datetime.now()

    def get_time_from_timestring(self, time_string):
        time_float = convert_string_to_float(time_string)
        if time_float > 0:
            self._datetime = datetime.fromtimestamp(time_float)
        else:
            self.get_time_now()

    def get_time_from_slaxlog(self, formated_time):
        pass

    def __gt__(self, time_object_2):
        return self.datetime > time_object_2.datetime

    @property
    def datetime(self):
        return self._datetime

    @property
    def time_float(self):
        return self._datetime.timestamp()

    @property
    def time_string(self):
        return convert_float_to_string(self.time_float)

    @property
    def formated_time(self):
        return

def prepare_file(folder, file):
    path = os.path.join(folder, file)
    with open(path, mode='a+') as f:
        pass

def test_new_file():
    file = 'created_for_test.txt'
    with open(file, mode='a+') as f:
        pass

def rename(folder, exist_name, new_name):
    filename =  os.path.join(folder, exist_name)
    new_filename = os.path.join(folder, new_name)
    os.rename(filename, new_filename)

def test_rename_file():
    folder = '/Users/wanwill/PycharmProjects/PTTV2'
    exist_name = 'created_for_test.txt'
    new_name = 'new_name.txt'
    rename(folder, exist_name, new_name)

def prepare_folder(folder, devices):
    """
    steps:
        create folder anyway
        if device file doesnot exist:
            create empty file
        move file name device to device_old

    :param folder:
    :return:
    """
    os.makedirs(folder, mode=0o777, exist_ok=True)
    for device in devices:
        prepare_file(folder=folder, file=device)
        rename(folder=folder, exist_name=device, new_name=f'{device}_old')
    return


def get_slax_log(project_name, folder, time_string):
    site_type, region, devices = get_type_region_devices_from_project(project_name)
    username = 'porttest'
    password = pttv2_gen_pwd.pwd_of_project(project_name)
    cred = Credential(username=username, password=password)
    flag = False
    if site_type == cli_module.PTT_SITE_TYPE.FUN:
        flag = cli_module.gen_project_record(project_name, time_string, folder)
    elif site_type == cli_module.PTT_SITE_TYPE.PHXV3:
        flag = cli_module.get_slax_cli(devices, time_string, region, folder, cred=cred)
    elif site_type == cli_module.PTT_SITE_TYPE.CENTENNIAL:
        flag = cli_module.get_slax_cli(devices, time_string, region, folder, cred=cred, vendor=cli_module.DeviceType.cisco)

        #flag = cli_module.get_cisco_log_cli(devices, time_string, region, folder)
    return flag


def get_type_region_devices_from_project(project):
    return cli_module.get_type_region_devices_from_project(project)


def write_device_record_to_ddb(device, project_name, time_string, folder):
    file = f"{folder}/{device}"
    with open(file) as f:
        up_records = []
        for line in f:
            if ',up,' not in line:
                continue
            items_in_a_line = line.split(",")
            if len(items_in_a_line) != 5:
                continue
            up_records.append(items_in_a_line)

        record_id = DDB_RECORD_SEPERATION.join([project_name, time_string, device])
        record = cli_module.Record(record_id)
        record.update_record(up_records)


def get_slax_for_project(project_name, start_flag=False):
    if cli_module.is_project_complete(project_name):
        message = f"The '{project_name}' completed port testing task. No need to get log"
        print(Color.BLUE + message + Color.WHITE)
        return

    time_diff = TimeDiff()
    time_string = TimeObj().time_string
    folder = SLAX_LOG_SAVE_AT + '/' + project_name #time_string
    #folders = [folder]

    site_type, region, devices = get_type_region_devices_from_project(project_name)

    prepare_folder(folder, devices)

    get_slax_log(project_name, folder, time_string)


    if not start_flag:
        for device in devices:
            # if site_type == cli_module.PTT_SITE_TYPE.PHXV3 and cli_module.PTT:
            if site_type == cli_module.PTT_SITE_TYPE.CENTENNIAL:
                pass
            else:
                write_device_record_to_ddb(device, project_name, time_string, folder)

        message = f"the slax log saved in folder '{folder}'\n uploading to DDB"
        print(Color.WHITE + message)

    else:

        message = (f"history log saved in folder '{folder}'\n uploading to DDB"
                   f"the device log is cleared. Ready to do porttest."
                   )

        print(Color.WHITE + message)

    processing_time_in_second = time_diff.get_difference_in_seconds()
    cli_module.update_record_list(project_name, time_string, processing_time_in_second)

def test_get_slax_for_project():
    project_name = 'iad.ewr53@deploy745'
    get_slax_for_project(project_name)

def get_args():
    parser = argparse.ArgumentParser(description='get slax record from device')
    parser.add_argument('-p', '--project',
                        help='pls give project name format {reg}.{az}@{sim_id}')
    parser.add_argument('-s', '--start_porttest', action='store_true',
                        help='run with -s, before onsite engineer insert fiber')

    return parser.parse_args()

def main():

    args = get_args()
    project_name = args.project
    start_flag = args.start_porttest

    return get_slax_for_project(project_name, start_flag)

def do_test():
    project_name = "pdx.pdx1.8@demo"
    project = cli_module.Project(project_name)

if __name__ == '__main__':
    main()

