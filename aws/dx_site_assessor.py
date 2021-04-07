#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import sys
import os
import argparse
import logging
import math
import yaml
import datetime
from collections import OrderedDict, Counter

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

from dxd_tools_dev.site_assessment import dxbi_data, mx_car, site_assessment
from dxd_tools_dev.datastore import ddb
from isd_tools_dev.modules import nsm as nsm_isd
from dxd_tools_dev.modules import nsm as nsm_dxd
from dxd_tools_dev.cutsheet import cutsheet_operations
from dxd_tools_dev.portdata import border

mx_info = open('/apollo/env/DXDeploymentTools/pop/mx_info.yaml','r')
mx_info_dict = yaml.safe_load(mx_info)

regular_dx_pops = open('/apollo/env/DXDeploymentTools/pop/regular_dx_pop.yaml','r')
regular_dx_pops_dict = yaml.safe_load(regular_dx_pops)

small_pop = open('/apollo/env/DXDeploymentTools/pop/small_pioneer_pop.yaml','r')
small_pop_dict = yaml.safe_load(small_pop)

scale_info = open('/apollo/env/DXDeploymentTools/pop/scale_info.yaml','r')
scale_info_dict = yaml.safe_load(scale_info)

site = ''
new_ports = 0
capacity = {'small_car_pair':80,'medium_car_pair':275,'large_car_pair':550}
capacity_phoenix = {'small':160,'medium':320,'large':640}
pop_size = dict()
site_data = dict()
scaling_colors = ['YELLOW','RED','ORANGE']
bom_fpcs = list()

datefmt = '%d-%b-%y %H:%M:%S'

dxbi = dxbi_data.DxbiData()

class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HIGHGREEN = "\033[1;42m"

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='dx_site_assessor.py')
    main_parser.add_argument("-st", "--site", type=str, dest="site", required=True, help="Specify the site for assessment")
    main_parser.add_argument("-sp", "--speed", type=str, dest="speed", required=True, help="Specify the speed for which you want to run site assessment")
    return main_parser.parse_args()

def get_site_data(site):
    global site_data

    if site not in site_data:
        tc_pop_border_capacity_table = ddb.get_ddb_table('tc_pop_border_capacity_table')
        site_data = ddb.get_device_from_table(tc_pop_border_capacity_table,'Site',site.upper())

    return site_data

def evaluate_legacy_cars(legacy_car_scale_info,speed,site):
    global new_ports, bom_fpcs

    if not legacy_car_scale_info:
        print('{} - Legacy MX vc-car(s) in {} have no slots available to scale'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))
    else:
        cars = [device for device in legacy_car_scale_info]
        print('{} - Legacy MX vc-car(s) {} have available slots. Checking if they can be scaled'.format(datetime.datetime.utcnow().strftime(datefmt),cars))

        for device in legacy_car_scale_info:
            if legacy_car_scale_info[device]['scalable']:
                print('{} - Additional line cards can be inserted in {}, recommended FPCs {}'.format(datetime.datetime.utcnow().strftime(datefmt),device,legacy_car_scale_info[device]['recommended_fpcs']))
                for fpc in legacy_car_scale_info[device]['recommended_fpcs']:
                    bom_fpcs.append(legacy_car_scale_info[device]['recommended_fpcs'][fpc])

                if site.lower() in regular_dx_pops_dict:
                    util = site_assessment.get_dx_device_util_last_week([device])
                    site_data = get_site_data(site)

                    for item in site_data['Devices_Bandwidth_Gbps']:
                        if item['Name'] == device:
                            capacity = item['Bandwidth_Gbps']
                            number_br_int = len(item['interfaces'])

                    usage_percentage = util[device] / float(capacity) * 100

                    if usage_percentage > 85:
                        print('{} - {}{} <> border capacity is running at {}%. Line card insertion would require scaling {} <> border capacity{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,device,round(usage_percentage,2),device,bcolors.ENDC))
                    else:
                        print('{} - {} <> border capacity is running at {}%. Line card insertion does not require scaling backhaul'.format(datetime.datetime.utcnow().strftime(datefmt),device,round(usage_percentage,2)))

                    if number_br_int < 4:
                        print('{} - {}{} is striped to {} upstream devices (NAR). Stripe {} to 4 upstream devices{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,device,number_br_int,device,bcolors.ENDC))

                if site.lower() in small_pop_dict:
                    util = site_assessment.get_dx_device_util_last_week([device])
                    site_data = get_site_data(site)
                    primaryPop = small_pop_dict[site.lower()]['primaryPop']
                    backupPop = small_pop_dict[site.lower()]['backupPop']

                    cap_p = 0
                    len_p = 0
                    cap_b = 0
                    len_b = 0

                    for item in site_data['Devices_Bandwidth_Gbps']:
                        if item['Name'] == device:
                            for cap in item['interfaces']:
                                try:
                                    if primaryPop in cap['description']:
                                        cap_p += int(cap['bandwidth'])
                                        len_p += 1
                                    if backupPop in cap['description']:
                                        cap_b += int(cap['bandwidth'])
                                        len_b += 1
                                except:
                                    pass

                    if cap_p > 0:
                        usage_percentage = util[device] / float(cap_p) * 100

                        if usage_percentage > 85:
                            print('{} - {}{} <> border capacity is running at {}%. Line card insertion would require scaling {} <> border capacity{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,device,round(usage_percentage,2),device,bcolors.ENDC))
                        else:
                            print('{} - {} <> border capacity is running at {}%. Line card insertion does not require scaling backhaul'.format(datetime.datetime.utcnow().strftime(datefmt),device,round(usage_percentage,2)))

                        if (len_p + len_b) < 4:
                            print('{} - {}{} is striped to {} upstream devices (NAR). Stripe {} to 4 upstream devices{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,device,(len_p+len_b),device,bcolors.ENDC))

                for fpc in legacy_car_scale_info[device]['recommended_fpcs']:
                    new_ports += mx_info_dict[legacy_car_scale_info[device]['scb_model']][speed][legacy_car_scale_info[device]['recommended_fpcs'][fpc]]

            else:
                print('{} - Additional line cards cannot be inserted in {}, it has {} customer BGP sessions and {} ports in DirectConnect Dashboard'.format(datetime.datetime.utcnow().strftime(datefmt),device,legacy_car_scale_info[device]['bgp_session_count'],legacy_car_scale_info[device]['dxbi_port_count']))

        if new_ports > 0:
            print('{} - {} ports will be added by inserting line cards into legacy MX cars'.format(datetime.datetime.utcnow().strftime(datefmt),new_ports))

def get_pop_sizes():
    global pop_size

    pop_size_table = ddb.get_ddb_table('pop_size')
    pop_size_table_scan = ddb.scan_full_table(pop_size_table)
    pop_size = {pop['PoP']:pop['Type'] for pop in pop_size_table_scan}

def print_devices_ports(devices_port_dict):
    for device in devices_port_dict:
        print()
        print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
        print('{}{}{}'.format(bcolors.OKGREEN,devices_port_dict[device],bcolors.ENDC))

def generate_bom_fpcs(bom_fpcs):
    bom_gen_fpcs = ''
    bom_fpcs = dict(Counter(bom_fpcs))
    for fpc in bom_fpcs:
        if fpc == 'MPC4E 3D 32XGE':
            bom_gen_fpcs += ' -lc_32x10g ' + str(bom_fpcs[fpc])
        if fpc == 'MPC 3D 16x 10GE':
            bom_gen_fpcs += ' -lc_16x10g ' + str(bom_fpcs[fpc])
        if fpc == 'MPCE Type 2 3D':
            bom_gen_fpcs += ' -lc_1g ' + str(bom_fpcs[fpc])
    return bom_gen_fpcs

def main():
    global site, new_ports, bom_fpcs

    cli_arguments = parse_args()
    site = cli_arguments.site.lower()
    legacy_cars = mx_car.get_site_mx_car_devices(site)
    new_car_prefix = site_assessment.get_new_car_prefix(site)

    get_pop_sizes()

    if site in regular_dx_pops_dict:
        border_site = regular_dx_pops_dict[site]
        speed = cli_arguments.speed.upper()
        chk_bmn_br = True

        br_tra_prefix = border_site + '-br-tra'
        vc_cor_prefix = border_site + '-vc-cor-b'
        br_kct_prefix = border_site + '-br-kct-p1'

        br_tra_list = cutsheet_operations.check_device_exists(br_tra_prefix)
        vc_cor_list = cutsheet_operations.check_device_exists(vc_cor_prefix)
        vc_cor_bricks = site_assessment.get_vc_cor_bricks(vc_cor_list)
        br_kct_list = cutsheet_operations.check_device_exists(br_kct_prefix)
        new_vc_cor_brick = site_assessment.get_new_vccor_brick(border_site.lower(),vc_cor_bricks)

        print('{}{}Running {} site assessment for {}{}'.format(bcolors.UNDERLINE,bcolors.BOLD,site.upper(),speed,bcolors.ENDC))

        site_data = dxbi.get_site_data(site)
        other_speed = mx_car.get_other_speed(speed)
        other_speed_estimated_ports = math.ceil(float(site_data[other_speed]['burn_rate_180_days']) * scale_info_dict['scaling_days'])
        devices_interfaces = mx_car.get_devices_interface_count(site)
        other_speed_available_interface_count = 0

        for device in devices_interfaces:
            try:
                other_speed_available_interface_count += int(devices_interfaces[device][other_speed]['available'])
            except KeyError:
                pass

        if not legacy_cars:
            print('{} - {} does not have legacy MX vc-car(s). Skipping line card insertion/swap'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))

        else:
            legacy_car_scale_info = mx_car.check_site_car_scaling(site,speed)
            evaluate_legacy_cars(legacy_car_scale_info,speed,site.upper())

            if new_ports == 0:
                if other_speed_available_interface_count < other_speed_estimated_ports:
                    print('{} - Not evaluating legacy MX vc-car(s) in {} for line card swap. {} available ports {} are less than estimated number of required ports {} in 2 years'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper(),other_speed,other_speed_available_interface_count,other_speed_estimated_ports))
                elif (((site_data[other_speed]['color'] not in scaling_colors) and (not site_data[other_speed]['sim'])) or (site_data[other_speed]['color'] == 'GREEN')):
                    print('{} - Checking legacy MX vc-car(s) in {} for line card swap'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))
                    swap, device_with_line_card = mx_car.check_card_swap(site.lower(),speed)
                    if not swap:
                        print('{} - Line cards cannot be swapped in legacy MX vc-car(s) at {}'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))
                    else:
                        for device in device_with_line_card:
                            new_ports += mx_info_dict[device_with_line_card[device]['scb']][speed][device_with_line_card[device]['fpc']]
                            bom_fpcs.append(device_with_line_card[device]['fpc'])
                else:
                    print('{} - Not evaluating legacy MX vc-car(s) in {} for line card swap. {} ports are {} at {}'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper(),other_speed,site_data[other_speed]['color'],site.upper()))

        try:
            out_of_ports_date = datetime.datetime.strptime(site_data[speed]['out_of_ports_date'],'%Y-%m-%d').date()
            today = datetime.date.today()
            delta = (out_of_ports_date - today).days

            if delta > 0:
                scaling_days = delta + scale_info_dict['scaling_days']
                scaling_months = round(scaling_days/30, 2)
            else:
                scaling_days = scale_info_dict['scaling_days']
                scaling_months = scale_info_dict['scaling_months']

        except ValueError:
            scaling_days = scale_info_dict['scaling_days']
            scaling_months = scale_info_dict['scaling_months']

        new_ports_estimated = math.ceil(float(site_data[speed]['burn_rate_180_days']) * scaling_days)
        site_size = capacity_phoenix[pop_size[site].lower()]

        if new_ports < new_ports_estimated:
            print('{} - Estimated {} ports needed in {} months: {}{}{}. Phoenix rack would need to be installed'.format(datetime.datetime.utcnow().strftime(datefmt),speed,scaling_months,bcolors.BOLD,new_ports_estimated,bcolors.ENDC))
            print('{} - {} is {} sized POP. Searching for available ports to support {}G for new Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper(),pop_size[site].lower(),capacity_phoenix[pop_size[site].lower()]))
            if vc_cor_bricks:
                print('{} - Found {} vc-cor brick(s) {} at {}'.format(datetime.datetime.utcnow().strftime(datefmt),len(vc_cor_bricks),vc_cor_bricks,border_site.upper()))
                vc_cor_speed, vc_cor_ports = site_assessment.get_vc_cor_ports(vc_cor_bricks,pop_size[site].lower())
                if vc_cor_ports:
                    vc_cor_brick = list(vc_cor_ports.keys())[0][:-3]
                    command_cutsheet = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                            + new_car_prefix + ' -cor ' + vc_cor_brick + ' -size ' + pop_size[site].lower()
                    for device in vc_cor_ports:
                        print()
                        print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                        print('{}{}{}'.format(bcolors.OKGREEN,vc_cor_ports[device],bcolors.ENDC))

                    chk_bmn = site_assessment.check_bmn(site)
                    bmn = ''
                    if not chk_bmn:
                        bmn = ' -bmn'

                    if bom_fpcs:
                        bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                    else:
                        bom_gen_fpcs = ''

                    print('To create cutsheet use {}'.format(command_cutsheet))
                    command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                            + site + ' -phx_o ' + vc_cor_speed + bmn + bom_gen_fpcs
                    print()
                    print('To create BOM use {}'.format(command_bom))

                elif br_tra_list and len(br_tra_list) >= 4:
                    print('{} - Could not find ports on existing vc-cor bricks in {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper()))
                    tra_chassis = {device: nsm_dxd.get_device_hardware_from_nsm(device)['Chassis'][0] for device in br_tra_list}
                    print('{} - Found required number of br-tra in {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper()))
                    all_br_tra_available_ports = cutsheet_operations.get_kct_available_ports(br_tra_list)
                    br_tra_10g,br_tra_40g_10g,br_tra_100g_10g,br_tra_100g = cutsheet_operations.get_10g_100g_ports_tra(all_br_tra_available_ports,capacity_phoenix[pop_size[site].lower()])
                    ptx_br_tra_10g_standard_dict,ptx_br_tra_100g_standard_dict,ptx_40g_ports_dict = site_assessment.get_dx_tra_ports(tra_chassis,all_br_tra_available_ports,br_tra_10g,br_tra_40g_10g,br_tra_100g_10g,br_tra_100g)

                    if pop_size[site].lower() == 'small':
                        ptx_40g_ports_dict = {device : ports for device, ports in ptx_40g_ports_dict.items() if len(ports) >= 2}

                        ptx_40g_ports_dict = OrderedDict(ptx_40g_ports_dict)

                        for device in ptx_br_tra_10g_standard_dict:
                            if device not in ptx_40g_ports_dict:
                                ptx_40g_ports_dict[device] = ptx_br_tra_10g_standard_dict[device]
                            else:
                                ptx_40g_ports_dict[device] = sorted(list(set(ptx_br_tra_10g_standard_dict[device]) | set(ptx_40g_ports_dict[device])))

                        ptx_br_tra_10g_standard_dict = ptx_40g_ports_dict

                        if len(ptx_br_tra_10g_standard_dict) >= 4:
                            for device in ptx_br_tra_10g_standard_dict:
                                channelized_ports = list()
                                for port in ptx_br_tra_10g_standard_dict[device]:
                                    if 'et' in port:
                                        channelized_ports.append(port + ':0')
                                        channelized_ports.append(port + ':1')
                                if channelized_ports:
                                    ptx_br_tra_10g_standard_dict.update({device:sorted(channelized_ports)})

                            print('{} - Required 10G ports found on br-tra. Ports available on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                            for device in ptx_br_tra_10g_standard_dict:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_10g_standard_dict[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            bmn = ''
                            if not chk_bmn:
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 10g ' + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

                        elif len(ptx_br_tra_100g_standard_dict) >= 4:
                            print('{} - Required 10G ports not found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt)))
                            print('{} - Required 100G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                            for device in ptx_br_tra_100g_standard_dict:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_100g_standard_dict[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            bmn = ''
                            if not chk_bmn:
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 100g ' + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

                        else:
                            print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                            print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                            if not br_kct_list:
                                print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                sys.exit()
                            else:
                                print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                                if not kct_ports:
                                    print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                    site_assessment.cut_tt_to_rbd(site,border_site)
                                    sys.exit()
                                else:
                                    for device in kct_ports:
                                        print()
                                        print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                        print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                                    chk_bmn = site_assessment.check_bmn(site)
                                    if site != border_site:
                                        chk_bmn_br = site_assessment.check_bmn(border_site)

                                    bmn = ''
                                    if (not chk_bmn) or (not chk_bmn_br):
                                        bmn = ' -bmn'

                                    if bom_fpcs:
                                        bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                                    else:
                                        bom_gen_fpcs = ''

                                    command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                            + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                                    print('To create cutsheet use {}'.format(command))
                                    command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                            + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                                    print()
                                    print('To create BOM use {}'.format(command_bom))

                    elif pop_size[site].lower() == 'medium':
                        ptx_40g_ports_dict = {device : ports for device, ports in ptx_40g_ports_dict.items() if len(ports) >= 2}

                        ptx_40g_ports_dict = OrderedDict(ptx_40g_ports_dict)

                        for device in ptx_br_tra_10g_standard_dict:
                            if device not in ptx_40g_ports_dict:
                                ptx_40g_ports_dict[device] = ptx_br_tra_10g_standard_dict[device]
                            else:
                                ptx_40g_ports_dict[device] = sorted(list(set(ptx_br_tra_10g_standard_dict[device]) | set(ptx_40g_ports_dict[device])))

                        ptx_br_tra_10g_standard_dict = ptx_40g_ports_dict

                        if len(ptx_br_tra_10g_standard_dict) >= 4:
                            for device in ptx_br_tra_10g_standard_dict:
                                channelized_ports = list()
                                for port in ptx_br_tra_10g_standard_dict[device]:
                                    if 'et' in port:
                                        channelized_ports.append(port + ':0')
                                        channelized_ports.append(port + ':1')
                                        channelized_ports.append(port + ':2')
                                        channelized_ports.append(port + ':3')
                                if channelized_ports:
                                    ptx_br_tra_10g_standard_dict.update({device:sorted(channelized_ports)})

                            print('{} - Required 10G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                            for device in ptx_br_tra_10g_standard_dict:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_10g_standard_dict[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            bmn = ''
                            if not chk_bmn:
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 10g ' + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

                        elif len(ptx_br_tra_100g_standard_dict) >= 4:
                            print('{} - Required 10G ports not found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt)))
                            print('{} - Required 100G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                            for device in ptx_br_tra_100g_standard_dict:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_100g_standard_dict[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            bmn = ''
                            if not chk_bmn:
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 100g ' + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

                        else:
                            print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                            print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                            if not br_kct_list:
                                print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                sys.exit()
                            else:
                                print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                                if not kct_ports:
                                    print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                    site_assessment.cut_tt_to_rbd(site,border_site)
                                    sys.exit()
                                else:
                                    for device in kct_ports:
                                        print()
                                        print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                        print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                                    chk_bmn = site_assessment.check_bmn(site)
                                    if site != border_site:
                                        chk_bmn_br = site_assessment.check_bmn(border_site)

                                    bmn = ''
                                    if (not chk_bmn) or (not chk_bmn_br):
                                        bmn = ' -bmn'

                                    if bom_fpcs:
                                        bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                                    else:
                                        bom_gen_fpcs = ''

                                    command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                            + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                                    print('To create cutsheet use {}'.format(command))
                                    command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                            + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                                    print()
                                    print('To create BOM use {}'.format(command_bom))

                    elif pop_size[site].lower() == 'large':
                        ptx_40g_ports_dict = {device : ports for device, ports in ptx_40g_ports_dict.items() if len(ports) >= 4}

                        ptx_40g_ports_dict = OrderedDict(ptx_40g_ports_dict)

                        for device in ptx_br_tra_10g_standard_dict:
                            if device not in ptx_40g_ports_dict:
                                ptx_40g_ports_dict[device] = ptx_br_tra_10g_standard_dict[device]
                            else:
                                ptx_40g_ports_dict[device] = sorted(list(set(ptx_br_tra_10g_standard_dict[device]) | set(ptx_40g_ports_dict[device])))

                        ptx_br_tra_10g_standard_dict = ptx_40g_ports_dict

                        if len(ptx_br_tra_10g_standard_dict) >= 4:
                            for device in ptx_br_tra_10g_standard_dict:
                                channelized_ports = list()
                                for port in ptx_br_tra_10g_standard_dict[device]:
                                    if 'et' in port:
                                        channelized_ports.append(port + ':0')
                                        channelized_ports.append(port + ':1')
                                        channelized_ports.append(port + ':2')
                                        channelized_ports.append(port + ':3')
                                if channelized_ports:
                                    ptx_br_tra_10g_standard_dict.update({device:sorted(channelized_ports)})

                            print('{} - Required 10G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                            for device in ptx_br_tra_10g_standard_dict:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_10g_standard_dict[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            bmn = ''
                            if not chk_bmn:
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 10g ' + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

                        elif len(ptx_br_tra_100g_standard_dict) >= 4:
                            print('{} - Required 10G ports not found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt)))
                            print('{} - Required 100G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                            for device in ptx_br_tra_100g_standard_dict:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_100g_standard_dict[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            bmn = ''
                            if not chk_bmn:
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 100g ' + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

                        else:
                            print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                            print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                            if not br_kct_list:
                                print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                sys.exit()
                            else:
                                print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                                if not kct_ports:
                                    print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                    site_assessment.cut_tt_to_rbd(site,border_site)
                                    sys.exit()
                                else:
                                    for device in kct_ports:
                                        print()
                                        print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                        print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                                    chk_bmn = site_assessment.check_bmn(site)
                                    if site != border_site:
                                        chk_bmn_br = site_assessment.check_bmn(border_site)

                                    bmn = ''
                                    if (not chk_bmn) or (not chk_bmn_br):
                                        bmn = ' -bmn'

                                    if bom_fpcs:
                                        bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                                    else:
                                        bom_gen_fpcs = ''

                                    command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                            + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                                    print('To create cutsheet use {}'.format(command))
                                    command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                            + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                                    print()
                                    print('To create BOM use {}'.format(command_bom))

                else:
                    print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                    print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                    if not br_kct_list:
                        print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                        sys.exit()
                    else:
                        print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                        kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                        if not kct_ports:
                            print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            site_assessment.cut_tt_to_rbd(site,border_site)
                            sys.exit()
                        else:
                            for device in kct_ports:
                                print()
                                print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                            chk_bmn = site_assessment.check_bmn(site)
                            if site != border_site:
                                chk_bmn_br = site_assessment.check_bmn(border_site)

                            bmn = ''
                            if (not chk_bmn) or (not chk_bmn_br):
                                bmn = ' -bmn'

                            if bom_fpcs:
                                bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                            else:
                                bom_gen_fpcs = ''

                            command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                    + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                            print('To create cutsheet use {}'.format(command))
                            command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                    + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                            print()
                            print('To create BOM use {}'.format(command_bom))

            elif br_tra_list and len(br_tra_list) >= 4:
                print('{} - Could not find ports on existing vc-cor bricks in {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper()))
                tra_chassis = {device: nsm_dxd.get_device_hardware_from_nsm(device)['Chassis'][0] for device in br_tra_list}
                print('{} - Found required number of br-tra in {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper()))
                all_br_tra_available_ports = cutsheet_operations.get_kct_available_ports(br_tra_list)
                br_tra_10g,br_tra_40g_10g,br_tra_100g_10g,br_tra_100g = cutsheet_operations.get_10g_100g_ports_tra(all_br_tra_available_ports,capacity_phoenix[pop_size[site].lower()])
                ptx_br_tra_10g_standard_dict,ptx_br_tra_100g_standard_dict,ptx_40g_ports_dict = site_assessment.get_dx_tra_ports(tra_chassis,all_br_tra_available_ports,br_tra_10g,br_tra_40g_10g,br_tra_100g_10g,br_tra_100g)

                if pop_size[site].lower() == 'small':
                    ptx_40g_ports_dict = {device : ports for device, ports in ptx_40g_ports_dict.items() if len(ports) >= 2}

                    ptx_40g_ports_dict = OrderedDict(ptx_40g_ports_dict)

                    for device in ptx_br_tra_10g_standard_dict:
                        if device not in ptx_40g_ports_dict:
                            ptx_40g_ports_dict[device] = ptx_br_tra_10g_standard_dict[device]
                        else:
                            ptx_40g_ports_dict[device] = sorted(list(set(ptx_br_tra_10g_standard_dict[device]) | set(ptx_40g_ports_dict[device])))

                    ptx_br_tra_10g_standard_dict = ptx_40g_ports_dict

                    if len(ptx_br_tra_10g_standard_dict) >= 4:
                        for device in ptx_br_tra_10g_standard_dict:
                            channelized_ports = list()
                            for port in ptx_br_tra_10g_standard_dict[device]:
                                if 'et' in port:
                                    channelized_ports.append(port + ':0')
                                    channelized_ports.append(port + ':1')
                            if channelized_ports:
                                ptx_br_tra_10g_standard_dict.update({device:sorted(channelized_ports)})

                        print('{} - Required 10G ports found on br-tra. Ports available on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                        for device in ptx_br_tra_10g_standard_dict:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_10g_standard_dict[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        bmn = ''
                        if not chk_bmn:
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 10g ' + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    elif len(ptx_br_tra_100g_standard_dict) >= 4:
                        print('{} - Required 10G ports not found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt)))
                        print('{} - Required 100G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                        for device in ptx_br_tra_100g_standard_dict:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_100g_standard_dict[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        bmn = ''
                        if not chk_bmn:
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 100g ' + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    else:
                        print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                        print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                        if not br_kct_list:
                            print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            sys.exit()
                        else:
                            print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                            if not kct_ports:
                                print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                site_assessment.cut_tt_to_rbd(site,border_site)
                                sys.exit()
                            else:
                                for device in kct_ports:
                                    print()
                                    print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                    print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                                chk_bmn = site_assessment.check_bmn(site)
                                if site != border_site:
                                    chk_bmn_br = site_assessment.check_bmn(border_site)

                                bmn = ''
                                if (not chk_bmn) or (not chk_bmn_br):
                                    bmn = ' -bmn'

                                if bom_fpcs:
                                    bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                                else:
                                    bom_gen_fpcs = ''

                                command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                        + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                                print('To create cutsheet use {}'.format(command))
                                command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                        + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                                print()
                                print('To create BOM use {}'.format(command_bom))

                elif pop_size[site].lower() == 'medium':
                    ptx_40g_ports_dict = {device : ports for device, ports in ptx_40g_ports_dict.items() if len(ports) >= 2}

                    ptx_40g_ports_dict = OrderedDict(ptx_40g_ports_dict)

                    for device in ptx_br_tra_10g_standard_dict:
                        if device not in ptx_40g_ports_dict:
                            ptx_40g_ports_dict[device] = ptx_br_tra_10g_standard_dict[device]
                        else:
                            ptx_40g_ports_dict[device] = sorted(list(set(ptx_br_tra_10g_standard_dict[device]) | set(ptx_40g_ports_dict[device])))

                    ptx_br_tra_10g_standard_dict = ptx_40g_ports_dict

                    if len(ptx_br_tra_10g_standard_dict) >= 4:
                        for device in ptx_br_tra_10g_standard_dict:
                            channelized_ports = list()
                            for port in ptx_br_tra_10g_standard_dict[device]:
                                if 'et' in port:
                                    channelized_ports.append(port + ':0')
                                    channelized_ports.append(port + ':1')
                                    channelized_ports.append(port + ':2')
                                    channelized_ports.append(port + ':3')
                            if channelized_ports:
                                ptx_br_tra_10g_standard_dict.update({device:sorted(channelized_ports)})

                        print('{} - Required 10G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                        for device in ptx_br_tra_10g_standard_dict:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_10g_standard_dict[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        bmn = ''
                        if not chk_bmn:
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 10g ' + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    elif len(ptx_br_tra_100g_standard_dict) >= 4:
                        print('{} - Required 10G ports not found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt)))
                        print('{} - Required 100G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                        for device in ptx_br_tra_100g_standard_dict:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_100g_standard_dict[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        bmn = ''
                        if not chk_bmn:
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 100g ' + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    else:
                        print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                        print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                        if not br_kct_list:
                            print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            sys.exit()
                        else:
                            print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                            if not kct_ports:
                                print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                site_assessment.cut_tt_to_rbd(site,border_site)
                                sys.exit()
                            else:
                                for device in kct_ports:
                                    print()
                                    print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                    print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                                chk_bmn = site_assessment.check_bmn(site)
                                if site != border_site:
                                    chk_bmn_br = site_assessment.check_bmn(border_site)

                                bmn = ''
                                if (not chk_bmn) or (not chk_bmn_br):
                                    bmn = ' -bmn'

                                if bom_fpcs:
                                    bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                                else:
                                    bom_gen_fpcs = ''

                                command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                        + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                                print('To create cutsheet use {}'.format(command))
                                command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                        + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                                print()
                                print('To create BOM use {}'.format(command_bom))

                elif pop_size[site].lower() == 'large':
                    ptx_40g_ports_dict = {device : ports for device, ports in ptx_40g_ports_dict.items() if len(ports) >= 4}

                    ptx_40g_ports_dict = OrderedDict(ptx_40g_ports_dict)

                    for device in ptx_br_tra_10g_standard_dict:
                        if device not in ptx_40g_ports_dict:
                            ptx_40g_ports_dict[device] = ptx_br_tra_10g_standard_dict[device]
                        else:
                            ptx_40g_ports_dict[device] = sorted(list(set(ptx_br_tra_10g_standard_dict[device]) | set(ptx_40g_ports_dict[device])))

                    ptx_br_tra_10g_standard_dict = ptx_40g_ports_dict

                    if len(ptx_br_tra_10g_standard_dict) >= 4:
                        for device in ptx_br_tra_10g_standard_dict:
                            channelized_ports = list()
                            for port in ptx_br_tra_10g_standard_dict[device]:
                                if 'et' in port:
                                    channelized_ports.append(port + ':0')
                                    channelized_ports.append(port + ':1')
                                    channelized_ports.append(port + ':2')
                                    channelized_ports.append(port + ':3')
                            if channelized_ports:
                                ptx_br_tra_10g_standard_dict.update({device:sorted(channelized_ports)})

                        print('{} - Required 10G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                        for device in ptx_br_tra_10g_standard_dict:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_10g_standard_dict[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        bmn = ''
                        if not chk_bmn:
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 10g ' + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    elif len(ptx_br_tra_100g_standard_dict) >= 4:
                        print('{} - Required 10G ports not found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt)))
                        print('{} - Required 100G ports found on br-tra'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.OKGREEN,bcolors.ENDC))
                        for device in ptx_br_tra_100g_standard_dict:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,ptx_br_tra_100g_standard_dict[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        bmn = ''
                        if not chk_bmn:
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -site ' + border_site.lower() + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 100g ' + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    else:
                        print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                        print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                        if not br_kct_list:
                            print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            sys.exit()
                        else:
                            print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                            kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                            if not kct_ports:
                                print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                                site_assessment.cut_tt_to_rbd(site,border_site)
                                sys.exit()
                            else:
                                for device in kct_ports:
                                    print()
                                    print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                                    print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                                chk_bmn = site_assessment.check_bmn(site)
                                if site != border_site:
                                    chk_bmn_br = site_assessment.check_bmn(border_site)

                                bmn = ''
                                if (not chk_bmn) or (not chk_bmn_br):
                                    bmn = ' -bmn'

                                if bom_fpcs:
                                    bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                                else:
                                    bom_gen_fpcs = ''

                                command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                        + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                                print('To create cutsheet use {}'.format(command))
                                command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                        + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                                print()
                                print('To create BOM use {}'.format(command_bom))

            else:
                print('{} - {}Required ports not available on br-tra{}'.format(datetime.datetime.utcnow().strftime(datefmt),bcolors.FAIL,bcolors.ENDC))
                print('{} - New vc-cor Brick would need to be installed at {}. Checking for ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),border_site.upper(),br_kct_prefix))
                if not br_kct_list:
                    print('{} - {} does not exist. Phoenix Renaissance cannot be deployed'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                    sys.exit()
                else:
                    print('{} - Searching for available ports on {}'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                    kct_speed, kct_ports = site_assessment.get_br_kct_ports(br_kct_list)
                    if not kct_ports:
                        print('{} - Ports on {} could not be found to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),br_kct_prefix))
                        site_assessment.cut_tt_to_rbd(site,border_site)
                        sys.exit()
                    else:
                        for device in kct_ports:
                            print()
                            print('{}{}{}{}'.format(bcolors.BOLD,bcolors.UNDERLINE,device,bcolors.ENDC))
                            print('{}{}{}'.format(bcolors.OKGREEN,kct_ports[device],bcolors.ENDC))

                        chk_bmn = site_assessment.check_bmn(site)
                        if site != border_site:
                            chk_bmn_br = site_assessment.check_bmn(border_site)

                        bmn = ''
                        if (not chk_bmn) or (not chk_bmn_br):
                            bmn = ' -bmn'

                        if bom_fpcs:
                            bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                        else:
                            bom_gen_fpcs = ''

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -cor ' + new_vc_cor_brick + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_regular -st ' \
                                + site + ' -phx_o 10g ' + '-cor -cor_o ' + kct_speed + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

        else:
            print('{} - Estimated {} ports needed in {} months: {} are less than ports made available by line card insertion: {} in legacy MX vc-cars. Phoenix rack not needed'.format(datetime.datetime.utcnow().strftime(datefmt),speed,scaling_months,new_ports_estimated,new_ports))

    elif site in small_pop_dict:
        border_site_p1 = small_pop_dict[site]['primaryPop'].lower()
        border_site_p2 = small_pop_dict[site]['backupPop'].lower()

        speed = cli_arguments.speed.upper()

        br_tra_p1_prefix = border_site_p1 + '-br-tra'
        vc_cor_p1_prefix = border_site_p1 + '-vc-cor-b'
        br_kct_p1_prefix = border_site_p1 + '-br-kct-p1'

        br_tra_p2_prefix = border_site_p2 + '-br-tra'
        vc_cor_p2_prefix = border_site_p2 + '-vc-cor-b'
        br_kct_p2_prefix = border_site_p2 + '-br-kct-p1'

        vc_dar_prefix = site + '-vc-dar-r'
        vc_car_prefix = site + '-vc-car-'

        br_tra_p1_list = cutsheet_operations.check_device_exists(br_tra_p1_prefix)
        br_tra_p2_list = cutsheet_operations.check_device_exists(br_tra_p2_prefix)
        vc_cor_p1_list = cutsheet_operations.check_device_exists(vc_cor_p1_prefix)
        vc_cor_p1_bricks = site_assessment.get_vc_cor_bricks(vc_cor_p1_list)
        vc_cor_p2_list = cutsheet_operations.check_device_exists(vc_cor_p2_prefix)
        vc_cor_p2_bricks = site_assessment.get_vc_cor_bricks(vc_cor_p2_list)
        br_kct_p1_list = cutsheet_operations.check_device_exists(br_kct_p1_prefix)
        br_kct_p2_list = cutsheet_operations.check_device_exists(br_kct_p2_prefix)
        new_vc_cor_p1_brick = site_assessment.get_new_vccor_brick(border_site_p1.lower(),vc_cor_p1_bricks)
        new_vc_cor_p2_brick = site_assessment.get_new_vccor_brick(border_site_p2.lower(),vc_cor_p2_bricks)

        vc_car_list = cutsheet_operations.check_device_exists(vc_car_prefix)
        vc_dar_list = cutsheet_operations.check_device_exists(vc_dar_prefix)
        existing_vc_dars = ','.join(vc_dar_list)
        new_vc_dars = vc_dar_prefix + '1,' + vc_dar_prefix + '2,' + vc_dar_prefix + '3,' + vc_dar_prefix + '4'

        cent_car_list = [car for car in vc_car_list if re.match('.*-v(2|5)-.*',car)]
        non_cent_car_list = [car for car in vc_car_list if not re.match('.*-v(2|5)-.*',car)]

        print('{}{}Running {} site assessment for {}{}'.format(bcolors.UNDERLINE,bcolors.BOLD,site.upper(),speed,bcolors.ENDC))

        site_data = dxbi.get_site_data(site)
        other_speed = mx_car.get_other_speed(speed)
        other_speed_estimated_ports = math.ceil(float(site_data[other_speed]['burn_rate_180_days']) * scale_info_dict['scaling_days'])
        devices_interfaces = mx_car.get_devices_interface_count(site)
        other_speed_available_interface_count = 0

        for device in devices_interfaces:
            try:
                other_speed_available_interface_count += int(devices_interfaces[device][other_speed]['available'])
            except KeyError:
                pass

        if not legacy_cars:
            print('{} - {} does not have legacy MX vc-car(s). Skipping line card insertion/swap'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))

        else:
            legacy_car_scale_info = mx_car.check_site_car_scaling(site,speed)
            evaluate_legacy_cars(legacy_car_scale_info,speed,site.upper())

            if new_ports == 0:
                if other_speed_available_interface_count < other_speed_estimated_ports:
                    print('{} - Not evaluating legacy MX vc-car(s) in {} for line card swap. {} available ports {} are less than estimated number of required ports {} in 2 years'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper(),other_speed,other_speed_available_interface_count,other_speed_estimated_ports))
                elif (((site_data[other_speed]['color'] not in scaling_colors) and (not site_data[other_speed]['sim'])) or (site_data[other_speed]['color'] == 'GREEN')):
                    print('{} - Checking legacy MX vc-car(s) in {} for line card swap'. format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))
                    swap, device_with_line_card = mx_car.check_card_swap(site.lower(),speed)
                    if not swap:
                        print('{} - Line cards cannot be swapped in legacy MX vc-car(s) at {}'. format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))
                    else:
                        for device in device_with_line_card:
                            new_ports += mx_info_dict[device_with_line_card[device]['scb']][speed][device_with_line_card[device]['fpc']]
                            bom_fpcs.append(device_with_line_card[device]['fpc'])
                else:
                    print('{} - Not evaluating legacy MX vc-car(s) in {} for line card swap. {} ports are {} at {}'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper(),other_speed,site_data[other_speed]['color'],site.upper()))

        try:
            out_of_ports_date = datetime.datetime.strptime(site_data[speed]['out_of_ports_date'],'%Y-%m-%d').date()
            today = datetime.date.today()
            delta = (out_of_ports_date - today).days

            if delta > 0:
                scaling_days = delta + scale_info_dict['scaling_days']
                scaling_months = round(scaling_days/30, 2)
            else:
                scaling_days = scale_info_dict['scaling_days']
                scaling_months = scale_info_dict['scaling_months']

        except ValueError:
            scaling_days = scale_info_dict['scaling_days']
            scaling_months = scale_info_dict['scaling_months']

        new_ports_estimated = math.ceil(float(site_data[speed]['burn_rate_180_days']) * scaling_days)
        site_size = capacity_phoenix[pop_size[site].lower()]

        if new_ports < new_ports_estimated:
            print('{} - Estimated {} ports needed in {} months: {}{}{}. Phoenix rack would need to be installed'.format(datetime.datetime.utcnow().strftime(datefmt),speed,scaling_months,bcolors.BOLD,new_ports_estimated,bcolors.ENDC))

            number_of_vc_car_pairs = cutsheet_operations.validate_existing_vc_car_pair(non_cent_car_list)
            cap_on_dar_for_existing_car_pair = cutsheet_operations.get_existing_car_capacity_for_dar(number_of_vc_car_pairs,pop_size[site].lower())
            total_dar_capacity_for_all_car_pairs = cutsheet_operations.get_total_dar_capacity_for_all_car(cap_on_dar_for_existing_car_pair,pop_size[site].lower())

            if cent_car_list:
                total_dar_capacity_for_all_car_pairs = total_dar_capacity_for_all_car_pairs + 1200

            total_dar_capacity_for_all_car_pairs_bytes = total_dar_capacity_for_all_car_pairs * 1000
            print('{} - Required vc-dar uplink capacity to each parent - {}G'.format(datetime.datetime.utcnow().strftime(datefmt),total_dar_capacity_for_all_car_pairs))

            if vc_dar_list:
                if len(vc_dar_list) != 4:
                    print('{} - {} has {} vc-dars. It needs 4 vc-dars. Site assessment cannot work, exiting'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper(),str(len(vc_dar_list))))
                    sys.exit()
                else:
                    print('{} - vc-dars exist. Verifying capacity between vc-dar <> br-tra/vc-cor'.format(datetime.datetime.utcnow().strftime(datefmt)))
                    vc_dar_port_map_list = cutsheet_operations.get_vc_cor_port_map(vc_dar_list)
                    vc_dar_p1_tra_capacity = cutsheet_operations.get_vc_dar_vccor_brick_capacity(vc_dar_port_map_list,br_tra_p1_prefix)
                    vc_dar_p1_vccor_capacity = cutsheet_operations.get_vc_dar_vccor_brick_capacity(vc_dar_port_map_list,vc_cor_p1_prefix)
                    vc_dar_p2_tra_capacity = cutsheet_operations.get_vc_dar_vccor_brick_capacity(vc_dar_port_map_list,br_tra_p2_prefix)
                    vc_dar_p2_vccor_capacity = cutsheet_operations.get_vc_dar_vccor_brick_capacity(vc_dar_port_map_list,vc_cor_p2_prefix)
                    vc_dar_p1_tra_vccor_capacity = vc_dar_p1_tra_capacity + vc_dar_p1_vccor_capacity
                    vc_dar_p2_tra_vccor_capacity = vc_dar_p2_tra_capacity + vc_dar_p2_vccor_capacity

                    if vc_dar_p1_tra_vccor_capacity >= total_dar_capacity_for_all_car_pairs_bytes and vc_dar_p2_tra_vccor_capacity >= total_dar_capacity_for_all_car_pairs_bytes:
                        print('{} - br-tra/vc-cor <> vc-dar in {} capacity is {}G'.format(datetime.datetime.utcnow().strftime(datefmt),border_site_p1.upper(),int(vc_dar_p1_tra_vccor_capacity/1000)))
                        print('{} - br-tra/vc-cor <> vc-dar in {} capacity is {}G'.format(datetime.datetime.utcnow().strftime(datefmt),border_site_p2.upper(),int(vc_dar_p2_tra_vccor_capacity/1000)))
                    else:
                        print('{} - br-tra/vc-cor <> vc-dar in {} capacity is {}G'.format(datetime.datetime.utcnow().strftime(datefmt),border_site_p1.upper(),int(vc_dar_p1_tra_vccor_capacity/1000)))
                        print('{} - br-tra/vc-cor <> vc-dar in {} capacity is {}G'.format(datetime.datetime.utcnow().strftime(datefmt),border_site_p2.upper(),int(vc_dar_p2_tra_vccor_capacity/1000)))
                        print('{} - Scale VC-DAR uplink capacity to {}G or more in both parent site(s)'.format(datetime.datetime.utcnow().strftime(datefmt),total_dar_capacity_for_all_car_pairs))

                    print('{} - Fetching 100G ports from {} to support Phoenix'.format(datetime.datetime.utcnow().strftime(datefmt),vc_dar_list))
                    all_vc_dar_available_ports = cutsheet_operations.get_vc_cor_available_ports(vc_dar_port_map_list)
                    vc_dar_car_ports = cutsheet_operations.get_vc_cor_port_for_car(all_vc_dar_available_ports)
                    vc_dar_ports = site_assessment.get_vc_dar_100g_ports_phoenix(vc_dar_car_ports)

                    for device in vc_dar_ports:
                        if len(vc_dar_ports[device]) < 2:
                            print('{} - Existing vc-dars do not have ports. HD vc-dars need to be installed. HD vc-dars not supported by this script. Exiting'.format(datetime.datetime.utcnow().strftime(datefmt)))
                            sys.exit()
                    
                    print_devices_ports(vc_dar_ports)
                    chk_bmn = site_assessment.check_bmn(site)
                    bmn = ''
                    if not chk_bmn:
                        bmn = ' -bmn'

                    if bom_fpcs:
                        bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                    else:
                        bom_gen_fpcs = ''

                    command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_phoenix_renaissance -car ' \
                            + new_car_prefix + ' -site_p1 ' + border_site_p1 + ' -site_p2 ' + border_site_p2 + \
                            ' -dar ' + existing_vc_dars + ' -size ' + pop_size[site].lower()
                    print('To create cutsheet use {}'.format(command))
                    command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_dx_small -st ' \
                            + site + bmn + bom_gen_fpcs
                    print()
                    print('To create BOM use {}'.format(command_bom))

            elif not vc_dar_list:
                chk_bmn = site_assessment.check_bmn(site)
                bmn = ''

                if bom_fpcs:
                    bom_gen_fpcs = generate_bom_fpcs(bom_fpcs)
                else:
                    bom_gen_fpcs = ''

                print('{} - vc-dars do not exist. vc-dar <> uplink capacity needed for this deployment is {}G'.format(datetime.datetime.utcnow().strftime(datefmt),total_dar_capacity_for_all_car_pairs))
                dar_uplink_capacity_needed = cutsheet_operations.get_dar_uplink_capacity_supported(total_dar_capacity_for_all_car_pairs)
                vc_cor_p1_bricks = site_assessment.get_vc_cor_bricks(vc_cor_p1_list)
                vc_cor_p2_bricks = site_assessment.get_vc_cor_bricks(vc_cor_p2_list)
                vc_cor_p1_speed, vc_cor_p1_ports = site_assessment.get_vc_cor_ports_for_small_pop(vc_cor_p1_bricks,dar_uplink_capacity_needed)
                vc_cor_p2_speed ,vc_cor_p2_ports = site_assessment.get_vc_cor_ports_for_small_pop(vc_cor_p2_bricks,dar_uplink_capacity_needed)

                if vc_cor_p1_ports and vc_cor_p2_ports:
                    vc_cor_p1_brick = list(vc_cor_p1_ports.keys())[0][:-3]
                    vc_cor_p2_brick = list(vc_cor_p2_ports.keys())[0][:-3]
                    print_devices_ports(vc_cor_p1_ports)
                    print_devices_ports(vc_cor_p2_ports)

                    if not chk_bmn:
                        bmn = ' -bmn'

                    command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_small_pop_phoenix_renaissance -car ' \
                              + new_car_prefix + ' -cor_p1 ' + vc_cor_p1_brick + ' -cor_p2 ' + vc_cor_p2_brick + \
                              ' -dar ' + new_vc_dars + ' -size ' + pop_size[site].lower()
                    print('To create cutsheet use {}'.format(command))
                    command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_dx_small -st ' \
                            + site + ' -dar -dar_o '+ vc_cor_p1_speed + bmn + bom_gen_fpcs
                    print()
                    print('To create BOM use {}'.format(command_bom))

                else:
                    tra_p1_chassis = {device: nsm_dxd.get_device_hardware_from_nsm(device)['Chassis'][0] for device in br_tra_p1_list}
                    tra_p2_chassis = {device: nsm_dxd.get_device_hardware_from_nsm(device)['Chassis'][0] for device in br_tra_p2_list}
                    all_br_tra_p1_available_ports = cutsheet_operations.get_kct_available_ports(br_tra_p1_list)
                    all_br_tra_p2_available_ports = cutsheet_operations.get_kct_available_ports(br_tra_p2_list)

                    if (vc_cor_p2_ports) and (not vc_cor_p1_ports):
                        vc_cor_p2_brick = list(vc_cor_p2_ports.keys())[0][:-3]
                        print_devices_ports(vc_cor_p2_ports)
                        print()
                        speed_p1,p1,chk_bmn_p1 = site_assessment.evaluate_one_parent_tra_small_pop(border_site_p1,site,dar_uplink_capacity_needed,br_tra_p1_list,tra_p1_chassis,all_br_tra_p1_available_ports,br_kct_p1_list,br_kct_p1_prefix,new_vc_cor_p1_brick)

                        if 'vc-cor' in p1:
                            p1 = ' -cor_p1 ' + new_vc_cor_p1_brick
                            bom_p1 = ' -cor_p1 -cor_p1_o ' + speed_p1
                        else:
                            p1 = ' -site_p1 ' + border_site_p1
                            bom_p1 = ''

                        if (not chk_bmn) or (not chk_bmn_p1):
                            bmn = ' -bmn'

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_small_pop_phoenix_renaissance -car ' \
                                + new_car_prefix + p1 + ' -cor_p2 ' + vc_cor_p2_brick + ' -dar ' + new_vc_dars + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_dx_small -st ' \
                              + site + bom_p1 + ' -dar -dar_o ' + speed_p1 + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    elif (vc_cor_p1_ports) and (not vc_cor_p2_ports):
                        vc_cor_p1_brick = list(vc_cor_p1_ports.keys())[0][:-3]
                        print_devices_ports(vc_cor_p1_ports)
                        print()
                        speed_p2,p2,chk_bmn_p2 = site_assessment.evaluate_one_parent_tra_small_pop(border_site_p2,site,dar_uplink_capacity_needed,br_tra_p2_list,tra_p2_chassis,all_br_tra_p2_available_ports,br_kct_p2_list,br_kct_p2_prefix,new_vc_cor_p2_brick)

                        if 'vc-cor' in p2:
                            p2 = ' -cor_p2 ' + new_vc_cor_p2_brick
                            bom_p2 = ' -cor_p2 -cor_p2_o ' + speed_p2
                        else:
                            p2 = ' -site_p2 ' + border_site_p2
                            bom_p2 = ''

                        if (not chk_bmn) or (not chk_bmn_p2):
                            bmn = ' -bmn'

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_small_pop_phoenix_renaissance -car ' \
                                + new_car_prefix + ' -cor_p1 ' + vc_cor_p1_brick + p2 + ' -dar ' + new_vc_dars + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_dx_small -st ' \
                                + site + bom_p2 + ' -dar -dar_o ' + speed_p2 + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))

                    else:
                        speed_p1,p1,chk_bmn_p1 = site_assessment.evaluate_one_parent_tra_small_pop(border_site_p1,site,dar_uplink_capacity_needed,br_tra_p1_list,tra_p1_chassis,all_br_tra_p1_available_ports,br_kct_p1_list,br_kct_p1_prefix,new_vc_cor_p1_brick)
                        speed_p2,p2,chk_bmn_p2 = site_assessment.evaluate_one_parent_tra_small_pop(border_site_p2,site,dar_uplink_capacity_needed,br_tra_p2_list,tra_p2_chassis,all_br_tra_p2_available_ports,br_kct_p2_list,br_kct_p2_prefix,new_vc_cor_p2_brick)

                        if 'vc-cor' in p1:
                            p1 = ' -cor_p1 ' + new_vc_cor_p1_brick
                            bom_p2 = ' -cor_p1 -cor_p1_o ' + speed_p1
                        else:
                            p1 = ' -site_p1 ' + border_site_p1
                            bom_p1 = ''

                        if 'vc-cor' in p2:
                             p2 = ' -cor_p2 ' + new_vc_cor_p2_brick
                             bom_p2 = ' -cor_p2 -cor_p2_o ' + speed_p2
                        else:
                            p2 = ' -site_p2 ' + border_site_p2
                            bom_p2 = ''

                        if (not chk_bmn) or (not chk_bmn_p1) or (not chk_bmn_p2):
                            bmn = ' -bmn'

                        command = '/apollo/env/DXDeploymentTools/bin/cutsheet_generator.py standard_small_pop_phoenix_renaissance -car ' \
                                + new_car_prefix + p1 + p2 + ' -dar ' + new_vc_dars + ' -size ' + pop_size[site].lower()
                        print('To create cutsheet use {}'.format(command))
                        command_bom = '/apollo/env/DXDeploymentTools/bin/bom_generator.py phoenix_dx_small -st ' \
                                + site + bom_p1 + bom_p2 + ' -dar -dar_o ' + speed_p1 + bmn + bom_gen_fpcs
                        print()
                        print('To create BOM use {}'.format(command_bom))
        else:
            print('{} - Estimated {} ports needed in {} months: {} are less than ports made available by line card insertion: {} in legacy MX vc-cars. Phoenix rack not needed'.format(datetime.datetime.utcnow().strftime(datefmt),speed,scaling_months,new_ports_estimated,new_ports))

    else:
        print('{} - Site assessment not supported for {}'.format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))
        print('{} - If site is regular, add it to https://code.amazon.com/packages/DXDeploymentTools/blobs/mainline/--/configuration/pop/regular_dx_pop.yaml'.format(datetime.datetime.utcnow().strftime(datefmt)))
        print('{} - If site is small/pioneer, add it to https://code.amazon.com/packages/DXDeploymentTools/blobs/mainline/--/configuration/pop/small_pioneer_pop.yaml'.format(datetime.datetime.utcnow().strftime(datefmt)))
        sys.exit()

if __name__ == '__main__':
    main()
