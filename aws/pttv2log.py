#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import dxd_tools_dev.modules.pttv2_cli_module as cli_module
import argparse
import os
import socket
from datetime import datetime

HOME = os.getenv("HOME")
SLAX_LOG_SAVE_AT = f'{HOME}/pttv2'

class Color:
    BLUE = '\033[36m'
    RED = '\033[31m'
    ORANGE = '\033[33m'
    BLACK ='\033[30m'
    GREY = '\033[37m'
    WHITE = '\033[0m'

class TypeNotice:
    ALARM = "ALARM"
    ERROR = "ERROR"
    MESSAGE = "MESSAGE"

def notice(type, message):
    sayit = f"[{type}] {message}"
    print(sayit)

def convert_float_to_string(timestamp:float):
    return str(timestamp)

def convert_string_to_float(timestring:str):
    result = 0
    try:
        result = float(timestring)
    except:
        notice(TypeNotice.ERROR, f"{timestring} is not right timestring")
    return result

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

def create_a_folder(folder):
    os.makedirs(folder, mode= 0o777, exist_ok=True)
    return

def get_log(devices, region, folders):
    cli_module.get_slax_cli(devices, region, folders)

def main():
    parser = argparse.ArgumentParser(description='get slax record from device')
    parser.add_argument('-r', '--region',
                        help='pls give region')
    parser.add_argument('-d', '--devices',
                        action="store", nargs='+',
                        dest="devices", required=True,
                        help='give exact one device name, seperated with space')

    time_string = TimeObj().time_string
    folder = SLAX_LOG_SAVE_AT + '/' + time_string
    folders = [folder]

    args = parser.parse_args()
    devices = args.devices
    region = args.region

    create_a_folder(folder)
    get_log(devices, region, folders)

    hostname = socket.gethostname()
    MESSAGE = f"please use copy to your pc with 'scp {hostname}:~/pttv2/{time_string}/* .'"
    print(Color.WHITE+MESSAGE)
if __name__ == '__main__':
    main()
