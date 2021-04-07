#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import argparse
import os
import sys
import logging
from dxd_tools_dev.modules import cm_creator, device_list_generator, colours

CM_TYPES = ['ibgp']

def create_args_parser():
    parser = argparse.ArgumentParser()
    cm_args = parser.add_argument_group()
    cm_args.add_argument('--cm_type', required=True, help='CM type to create')
    cm_args.add_argument('--new_devices', required=True, 
                         help='List of new devices to add. EG. iad2-vc-car-r1:1.1.1.1,iad2-vc-car-r2:2.2.2.2')
    cm_args.add_argument('--region', required=True, help='Region.')
    cm_args.add_argument('--mcm', required=True, help='CM number')
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase display output')
    
    return parser

def get_devices(query_type, region):
    return device_list_generator.main(query_type, region)
    
def validation(args):
    if args.cm_type not in CM_TYPES:
        print(colours.FAIL + 'The following list of cm types are supported: {}.'.format(CM_TYPES) + colours.ENDC )
        return False
    if not all('vc-car' in device for device in args.new_devices.split(',')):
        print(colours.FAIL + 'Currently only vc-car devices are supported.' + colours.ENDC)
        return False
    if not all(':' in device for device in args.new_devices.split(',')):
        print(colours.FAIL + 'Incorrect device syntax.' + colours.ENDC)
        return False

    return True

def main():
    parser = create_args_parser()
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    logging.debug('Validating user arguments')
    proceed = validation(args)
    logging.debug('User args validated. Continue: {}'.format(proceed))
    if args.cm_type == 'ibgp':
        if proceed:
            logging.debug('Getting list of devices')
            devices = get_devices('ibgp_query', args.region)
            logging.debug('Retrieved devices')
            cm_creator_obj = cm_creator.CmCreator(args.new_devices, 
                                                  args.region,
                                                  args.mcm)
            car_mesh = cm_creator_obj.get_ibgp_mesh_for_cars(devices)
            logging.debug('Creating variable file')
            cm_creator_obj.create_ibgp_mesh_var(car_mesh)
            print(colours.OKGREEN + 'Adding the following devices to the mesh: \n' + colours.ENDC)
            for device in car_mesh:
                print(device)
        else:
            sys.exit()

if __name__ == '__main__':
    main()
