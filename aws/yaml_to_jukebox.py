#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import logging
import re
import argparse
import yaml
from dxd_tools_dev.modules import jukebox
#from com.amazon.jukebox.portreservations import portReservations
from dxd_tools_dev.modules.utils import setup_logging, validate_file_exists


def parse_args():
    parser = argparse.ArgumentParser(description='''Upload Yaml file into Jukebox.\n
    wiki:TBD
    Examples:
    /apollo/env/DXDeploymentTools/bin/yaml_to_jukebox.py --yaml ~/DXYamls/nrt7.yaml
    ''', add_help=True, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-y', '--yaml', required=True, help='Path to yaml file, e.g. ~/DXYamls/nrt7.yaml')
    parser.add_argument('-e', '--execute', action='store_true', help='Uploads yaml data to Jukebox. If not specified, script runs in dryrun mode')
    return parser.parse_args()


def validate_input(args):
    """
    Validate user input
    :param args:
    :return:
    """
    validate_file_exists(args.yaml)
    if args.execute:
        logging.info('Script running in EXECUTE mode')
    else:
        logging.info('Script running in DRYRUN mode')


def get_link_type(z_hostname):
    """
    Returns L3 link type based on z_hostname
    :param z_hostname:
    :return:
    """
    link_type_table = [
        [r'(vc-(bar|edg|xlc|cir))', 'internal'],
        ['svc', 'ec2'],
        ['br-agg', 'border'],
        ]
    for link in link_type_table:
        if re.search(link[0], z_hostname):
            return link[1]


def add_device(device_dict, region):
    """
    Query Jukebox for device, else create coral device
    :param device_dict: dictionary for one device
    :param region:
    :return coral_device: jukebox coral device object
    """
    vendor = 'Juniper'
    global NEW_DEVICE
    try:  # Might need a better way to find if device exists
        logging.info('Querying Jukebox for {}'.format(device_dict['a_hostname']))
        NEW_DEVICE = False
        coral_device = jukebox.get_device_detail(device_dict['a_hostname'])
        return coral_device
    except TypeError:
        logging.info('{} not found in Jukebox, creating {}'.format(device_dict['a_hostname'], device_dict['a_hostname']))
        NEW_DEVICE = True
        return jukebox.create_coral_device(device_dict['a_hostname'],vendor,device_dict['model'],device_dict['serial'], device_dict['ipv4'],'',region)


def parse_cabling(a_device_dict, coral_device):
    """
    Parse cabling info for A-Device
    :param a_device_dict:
    :param coral_device:
    :return amended_cabling: Jukebox DeviceCabling object
    """
    a_hostname = a_device_dict['a_hostname']
    global ADD_CABLING
    ADD_CABLING = False
    amended_cabling = []
    existing_a_intf = []  # used to make sure new interfaces don't already exist in JB
    if NEW_DEVICE:
        existing_cabling = []
    elif not NEW_DEVICE:
        existing_cabling = coral_device.data.cabling
        for cable in existing_cabling:
            if cable.device_a_name == a_hostname:  # this condition is needed because JB returns mirrored cabling as well
                existing_a_intf.append(cable.device_a_interface_name)

    for z_index in a_device_dict['connections'].keys():
        z_hostname = a_device_dict['connections'][z_index]['z_hostname']
        if 'vc-svc' in z_hostname and a_device_dict['edge_rack'] == 'dori-s':  # skips cabling for vc-svc in vegemite racks
            continue
        if a_device_dict['connections'][z_index].get('a_interfaces'):
            logging.info('Parsing cabling: {} <> {}'.format(a_hostname, z_hostname))
            ADD_CABLING = True
            for index, a_intf in enumerate(a_device_dict['connections'][z_index]['a_interfaces']):
                z_intf = a_device_dict['connections'][z_index]['z_interfaces'][index]
                if a_intf in existing_a_intf:
                    logging.warning('{}:{} already exists, ignoring..'.format(a_hostname, a_intf))
                else:
                    amended_cabling = jukebox.device_cabling(a_intf, a_hostname, z_hostname, z_intf, existing_cabling)
        else:
            logging.info('Cabling not found: {} <> {}'.format(a_hostname, z_hostname))
    return amended_cabling


def parse_links(a_device_dict, coral_device):
    """
    Parse link info for A-Device
    :param a_device_dict:
    :param coral_device:
    :return amended_links: Jukebox DeviceLink object:
    """
    a_hostname = a_device_dict['a_hostname']
    global ADD_LINKS
    ADD_LINKS = False
    amended_links = []
    if NEW_DEVICE:
        existing_links = []
    elif not NEW_DEVICE:
        existing_links = coral_device.data.links
        for link in existing_links:
            if link.device_a_name == a_hostname:  # Needed because JB returns mirrored cabling as well
                existing_links.append(link.device_z_name)

    for z_index in a_device_dict['connections'].keys():
        z_hostname = a_device_dict['connections'][z_index]['z_hostname']
        csc_cidr = None  # Default is no csc_cidr, only exists towards br-aggs
        if 'es-svc' in z_hostname:  # skips layer 2 es-svc devices
            continue
        if a_device_dict['connections'][z_index].get('inet_cidr'):
            logging.info('Parsing link CIDRs: {} <> {}'.format(a_hostname, z_hostname))
            ADD_LINKS = True
            inet_cidr = a_device_dict['connections'][z_index]['inet_cidr']
            if z_hostname in existing_links:  # Checking link doesn't already exist
                logging.warning('{} to {} link already exists, ignoring..'.format(a_hostname, z_hostname))
            else:
                amended_links = jukebox.create_new_cidr_info(a_hostname, z_hostname, inet_cidr, csc_cidr, get_link_type(z_hostname), existing_links)
        else:
            logging.info('Link CIDR not found: {} to {}'.format(a_hostname, z_hostname))
    return amended_links


def upload_to_jukebox(coral_device, amended_cabling, amended_links, site, a_hostname):
    """
    Upload coral device to Jukebox
    :param coral_device:
    :param amended_cabling:
    :param amended_links:
    :param site:
    :param a_hostname:
    :return:
    """
    try:
        logging.info('Uploading {} data to Jukebox'.format(a_hostname))
        if NEW_DEVICE:
            jukebox.add_new_device_to_jb(coral_device, amended_cabling, amended_links, site)
        elif not NEW_DEVICE:
            if ADD_CABLING and ADD_LINKS:
                jukebox.edit_full_device(a_hostname, amended_cabling, amended_links)
            elif ADD_CABLING:
                jukebox.edit_jukebox_cabling(a_hostname, amended_cabling)
            elif ADD_LINKS:
                jukebox.edit_link_cidr(a_hostname, amended_links)
    except Exception as error:
        logging.error('Failed to upload {} to Jukebox'.format(a_hostname))
        logging.error(error)


def main():
    setup_logging()
    args = parse_args()
    validate_input(args)
    logging.info('Reading {}'.format(args.yaml))
    with open(args.yaml) as hambone_yaml:
        main_dict = yaml.load(hambone_yaml)

    for layer in main_dict['Devices'].keys():
        for a_index in main_dict['Devices'][layer].keys():
            coral_device = add_device(main_dict['Devices'][layer][a_index], main_dict['Region'])
            amended_cabling = parse_cabling(main_dict['Devices'][layer][a_index], coral_device)
            amended_links = parse_links(main_dict['Devices'][layer][a_index], coral_device)
            if args.execute:
                upload_to_jukebox(coral_device, amended_cabling, amended_links, main_dict['Site'], (main_dict['Devices'][layer][a_index]['a_hostname']))

if __name__ == "__main__":
    main()
