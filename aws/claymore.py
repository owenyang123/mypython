#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import argparse
from dxd_tools_dev.modules import jukebox,az
from isd_tools_dev.modules import hercules, utils
import logging
import sys
import re
import os

logging.basicConfig(level=logging.INFO)
logging.getLogger('bender.config.service.ConfigProvider').setLevel(logging.CRITICAL)

china_pop = ['bjs','pek','zhy','szx']

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='clamore.py', description='Automates Claymnore deployment tasks')
    subparsers = main_parser.add_subparsers(help='commands', dest='command')
    gbattr_parser = subparsers.add_parser('gb-attr', help='Creates br-agg attributes')
    gbattr_parser.add_argument("-d", "--devices", action="store", nargs='+', dest="devices", required=True, help="specify hostname of new vc-bars separated by space e.g cmh54-vc-bar-r101 cmh54-vc-bar-r102 cmh54-vc-bar-r103 cmh54-vc-bar-r104")
    gbattr_parser.add_argument("-p", "--path", action="store", dest="path", help="specify the output path for generated files e.g /home/ajijolao")

    jukebox = subparsers.add_parser('jukebox', help='update jukebox with device information')
    jukebox.add_argument("-m", "--mcm", action="store", nargs='+', dest="mcm", required=True, help="specify the MCM-ID for the cutsheet")


    dogfish = subparsers.add_parser('dogfish', help='updates dogfish with the p2p and loopback IPs')
    dogfish.add_argument("-m", "--mcm", action="store", nargs='+', dest="mcm", required=True, help="specify the MCM-ID for the cutsheet")

    return main_parser.parse_args()


def main():
    cli_arguments = parse_args()
    if cli_arguments.command == 'gb-attr':
        vc_bars = cli_arguments.devices
        if not cli_arguments.path:
            path = os.getenv("HOME")
        else:
            path = cli_arguments.path
        if os.path.exists('{}/GenevaBuilder'.format(path)):
            if vc_bars[0][:3] in china_pop:
                az.generate_gb_attr_bar(vc_bars,'{}/GenevaBuilder/targetspec/border-cn'.format(path))
            else:
                az.generate_gb_attr_bar(vc_bars,'{}/GenevaBuilder/targetspec/border'.format(path))
        else:
            logging.error('Check GenevaBuilder package exists in path {}'.format(path))


if __name__ == '__main__':
    main()
