#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import sys
import os
import argparse
import logging
from dxd_tools_dev.hambone import hambone
from isd_tools_dev.modules import hercules


china_pop = ['bjs','pek','zhy','szx']


logging.getLogger('bender.config.service.ConfigProvider').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO)


def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='afang.py', description='BR-AGG attr, Generate variable, config and diff files for hambone v2 migration')
    subparsers = main_parser.add_subparsers(help='commands', dest='command')
    migrate_parser = subparsers.add_parser('migrate', help='Hambone Migration Files')
    migrate_parser.add_argument("-d", "--devices", action="store", nargs='+', dest="devices", required=True, help="specify hostname of devices to be migrated  separated by space e.g iad12-vc-edg-r311 iad12-vc-edg-r312")
    migrate_parser.add_argument("-m", "--mcm", action="store", dest="mcm", required=True, help="specify MCM for hambone migration")
    migrate_parser.add_argument("-f", "--first_bar_router", action="store", dest="first_bar_router", required=True, help="specify the hostname of the first vc-bar router in the hambone version 2 being deployed")
    migrate_parser.add_argument("-w", "--width", action="store", dest="width", required=True, type=int, help="specify the number of hambone version 2 vc-bar in az")
    migrate_parser.add_argument("-p", "--path", action="store", dest="path", help="specify the output path for generated files e.g /home/ajijolao")
    gbattr_parser = subparsers.add_parser('gb-attr', help='Generates GB attributes for BR-AGGs towards BARs')
    gbattr_parser.add_argument("-d", "--devices", action="store", nargs='+', dest="devices", required=True, help="specify hostname of new vc-bar to be deployed  separated by space e.g iad12-vc-bar-r3 iad12-vc-bar-r4 iad12-vc-bar-r5 iad12-vc-bar-r6")
    gbattr_parser.add_argument("-p", "--path", action="store", dest="path", help="specify the path to GenevaBuilder package e.g /home/ajijolao")
    return main_parser.parse_args()

def validate_input():
    cli_arguments = parse_args()
    devices = cli_arguments.devices
    for device in devices:
        if not 'edg' in device and not 'cir' in device:
            print('{} Not a valid hambone client'.format(device))
            sys.exit(1)
    if not 'bar' in cli_arguments.first_bar_router:
        print('{} Not a valid bar'.format(cli_arguments.first_bar_router))
        sys.exit(1)
    return True

def create_ouput_dir():
    cli_arguments = parse_args()
    if not cli_arguments.path   :
        path = os.getcwd()
    else:
        path = cli_arguments.path
    ouput_dir='{}/{}'.format( path, cli_arguments.mcm)
    try:
        os.mkdir(ouput_dir)
        os.mkdir('{}/{}'.format(ouput_dir,'files'))
    except Exception as e:
        message = 'Could not create directory {}:  {}'.format(ouput_dir, e)
        logging.error(message)
        sys.exit(1)
    return ouput_dir

def config_files():
    cli_arguments = parse_args()
    ouput_dir = create_ouput_dir()
    width = cli_arguments.width
    az = cli_arguments.first_bar_router.split('-')[0]
    device_connections_list = []
    uplink_devices = hambone.get_uplink_devices(cli_arguments.devices[0])
    for device in cli_arguments.devices:
        device_connections = hambone.get_hambone_client_device_connections_var_format(device,cli_arguments.first_bar_router,width)
        device_connections_list.append(device_connections)
    print(device_connections_list)
    hb_2_vc_bars = hambone.get_new_hambome_v2_vc_bars(cli_arguments.first_bar_router,width)
    hambone.generate_variable_for_hambone_migration(ouput_dir,device_connections_list,uplink_devices,cli_arguments.mcm,cli_arguments.first_bar_router,width)
    for client_device in cli_arguments.devices:
        client_device_config = hercules.get_latest_config_for_device(client_device).decode("utf-8").split("\n")
        hambone.generate_hb_migration_config_file('{}/files'.format(ouput_dir), client_device_config, hb_2_vc_bars,  client_device)
        hambone.generate_hb_migration_remove_file('{}/files'.format(ouput_dir),client_device_config,client_device)
    for uplink_device in uplink_devices:
        uplink_device_ouput_dir='{}/files/{}'.format(ouput_dir, uplink_device)
        os.mkdir(uplink_device_ouput_dir)
    for  client_device in cli_arguments.devices:
        for uplink_device in uplink_devices:
            uplink_device_ouput_dir='{}/files/{}'.format(ouput_dir, uplink_device)
            if 'fab' in uplink_device:
                hambone.generate_hb_migration_fab_file(uplink_device_ouput_dir,uplink_device,client_device)
                hambone.generate_hb_migration_fab_diff_file(uplink_device_ouput_dir,uplink_device,client_device)
            elif 'mpe' in uplink_device:
                hambone.generate_hb_migration_mpe_config_file(uplink_device_ouput_dir,uplink_device,client_device)
                hambone.generate_hb_migration_mpe_diff_file(uplink_device_ouput_dir,uplink_device,client_device)
            elif 'br-agg' in uplink_device:
                hambone.generate_hb_migration_br_agg_config_file(uplink_device_ouput_dir,uplink_device,client_device)
                hambone.generate_hb_migration_br_agg_diff_file(uplink_device_ouput_dir,uplink_device,client_device)
def main():
    cli_arguments = parse_args()
    if cli_arguments.command == 'migrate':
        if validate_input():
            config_files()
    elif cli_arguments.command == 'gb-attr':
        vc_bars = cli_arguments.devices
        if not cli_arguments.path:
            path = os.getenv("HOME")
        else:
            path = cli_arguments.path
        if os.path.exists('{}/GenevaBuilder'.format(path)):
            if vc_bars[0][:3] in china_pop:
                hambone.generate_gb_attr_bar(vc_bars,'{}/GenevaBuilder/targetspec/border-cn'.format(path))
            else:
                hambone.generate_gb_attr_bar(vc_bars,'{}/GenevaBuilder/targetspec/border'.format(path))
        else:
            logging.error('Check GenevaBuilder package exists in path {}'.format(path))


if __name__ == '__main__':
    main()
