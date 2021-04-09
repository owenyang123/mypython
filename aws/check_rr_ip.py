#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import sys
import argparse
import logging
import time
from datetime import datetime
from dxd_tools_dev.modules import jukebox
from dxd_tools_dev.modules.jukebox import end_points
from dxd_tools_dev.modules.jukebox import get_all_devices_in_jukebox
from dxd_tools_dev.modules.jukebox import device_states

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    DARKYELLOW = '\033[0,33m'
    DARKGREEN = '\033[0,32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#functions
def get_rr_devices(devices):
    rrdevs = []
    a = ["hrr", "crr", "rrr"]
    for rrdevices in devices:
        for keys,values in rrdevices.items():
            if keys == "devices":
                for rr in values:
                    if len(rr.split('-')) > 2:
                        rrdev = rr.split('-')[2]
                        if any (x in rrdev for x in a):
                            rrdevs.append(rr)
    return rrdevs


def get_rr_loopback_address(rrdev):
    device_loopback = {}
    for rr in rrdev:
        try:
            ipv4 = jukebox.get_device_detail(rr).data.device.loopback_addresses[0].ipv4_address
        except Exception as e:
            logging.error(str(e))
            print (rr,ipv4)
        device_loopback[rr]=ipv4
    return device_loopback


def check_ip_address(ipaddresstocheck, rrdev):
    rrip = get_rr_loopback_address(rrdev)
    for keys,values in rrip.items():
        print ('{0}{1}'.format(keys,values))
        if ipaddresstocheck is str(values) or ipaddresstocheck == str(values):
            print ('{0}{1}{2}{3}{4}'.format(bcolors.FAIL,'This is a duplicate address: ', keys,values, bcolors.ENDC)) 
            sys.exit()
    print ('{0}{1}{2}'.format(bcolors.OKGREEN, 'No ip address conflicts have been found ', bcolors.ENDC))


def main():
    parser = argparse.ArgumentParser("IP of rr device to check")
    parser.add_argument('-ip', required=True, dest="ip", help="IP address provided for check")    
    args = parser.parse_args()
    now_time = datetime.now()
    print ("IP address to check: ", args.ip)
    devices = get_all_devices_in_jukebox(endpoint=end_points , device_states = device_states, devicetype = False)
    rrdev = get_rr_devices(devices)
    check_ip_address(args.ip, rrdev)
    finish_time = datetime.now()
    duration = finish_time - now_time
    minutes, seconds = divmod(duration.seconds, 60)
    print(
    bcolors.DARKYELLOW
    + "The script took {} minutes and {} seconds to run.".format(minutes, seconds)
    + bcolors.ENDC
    )

if __name__ == "__main__":
    main()

