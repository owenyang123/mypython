#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import pttv2_cli_module
from dxd_tools_dev.modules import pttv2_config_device
import logging
import argparse

def init_logging():
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)

    # make it print to the console.
    console = logging.StreamHandler()
    logger.addHandler(console)

    format_str = '%(asctime)s\t%(levelname)s -- %(processName)s %(filename)s:%(lineno)s -- %(message)s'
    console.setFormatter(logging.Formatter(format_str))

def get_args():
    parser = argparse.ArgumentParser(description='initial device for PTTV2 parameter input from yaml file')
    parser.add_argument('-y', '--yaml',
                        help='pls give yaml file as input')
    return parser.parse_args()

def is_device_not_in_service(device):
    result = pttv2_cli_module.find_device_in_service_in_jukebox([device])
    if result is None:
        return True
    return False


def main():
    init_logging()
    args = get_args()

    yaml_file = args.yaml
    dg = pttv2_config_device.DeviceGroup(yaml_file=yaml_file)
    dg.fast_config()

if __name__ == '__main__':
    main()
