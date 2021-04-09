#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import logging
import re
from multiprocessing import Pool

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

from dxd_tools_dev.portdata import portmodel
from dxd_tools_dev.modules import jukebox
from isd_tools_dev.modules import nsm
from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.modules.nsm import *
#from dxd_tools_dev.modules import telesto
from dxd_tools_dev.datastore import ddb

REGIONS = ['iad', 'pdx', 'bjs', 'fra', 'bom', 'hkg', 'nrt', 'cmh', 'arn', 'dub','syd', 'lhr', 'pek', 'yul', 'kix', 'corp', 'cdg', 'bah', 'zhy', 'sfo','sin', 'icn', 'gru', 'cpt', 'mxp']

def get_jb_dx_devices_region():
    devices_region = jukebox.get_all_devices_in_jukebox()
    dx_devices_region = []
    region_counter = 0
    for region in devices_region:
        dx_devices_region.append({})
        for device in region['devices']:
            site = device.split('-')[0]
            site_counter = 0
            item_counter =0
            if len(dx_devices_region) != 0:
                if not site in dx_devices_region[region_counter].keys():
                    dx_devices_region[region_counter][site] = {}
                    dx_devices_region[region_counter][site]['site_name'] = site
                    dx_devices_region[region_counter][site]['devices']=[device]
                    dx_devices_region[region_counter]['endpoint'] = region['endpoint']
                    dx_devices_region[region_counter]['region'] = region['endpoint']['region']
                else:
                    dx_devices_region[region_counter][site]['devices'].append(device)
            else:
                dx_devices_region[region_counter][site] = {}
                dx_devices_region[region_counter][site]['site_name'] = site
                print(dx_devices_region)
                dx_devices_region[region_counter][site]['devices']=[device]
                dx_devices_region[region_counter]['endpoint'] = region['endpoint']
                dx_devices_region[region_counter]['region'] = region['endpoint']['region']
                print(dx_devices_region)
        region_counter += 1
    return dx_devices_region


def get_jb_dx_devices_sites():
    devices_region = jukebox.get_devices_in_jukebox()
    dx_devices_sites = []
    counter = 0
    for region in devices_region:
        for device in region['devices']:
            site = device.split('-')[0]
            site_counter = 0
            item_counter =0
            if len(dx_devices_sites) != 0:
                for item in  dx_devices_sites:
                    if item['site'] == site:
                        site_counter +=1
                        break
                    item_counter +=1
                if site_counter == 0:
                    site_data = {'site': site , 'devices':[device], 'endpoint' : devices_region[counter]['endpoint']}
                    dx_devices_sites.append(site_data)
                else:
                    dx_devices_sites[item_counter]['devices'].append(device)
            else:
                site_data = {'site': site , 'devices':[device] , 'endpoint' : devices_region[counter]['endpoint']}
                dx_devices_sites.append(site_data)
        counter += 1
    return dx_devices_sites


def get_site_info(dx_devices_and_site):
    device_site = dx_devices_and_site['site']
    devices = dx_devices_and_site['devices']
    site_info = {'site' : device_site , 'devices' :[]}
    for device in devices:
        try:
            raw_data = nsm.get_raw_device_with_interfaces(device)
            device_raw_json = nsm.get_raw_device(device)
            availability_map = dict()
            portmodel.build_device_port_availability_map(availability_map,device,device_raw_json)
            device_info = {'os_version' : raw_data['software']['version'], 'model': raw_data['model'], 'last_poll_success': raw_data['last_poll_success'], 'nsm_state': raw_data['state']['lifecycle_status'],
            'name' :  raw_data['name'], 'ports':  availability_map , 'polling_status': raw_data['polling_status'], 'owner': raw_data['owner'] , 'layer' : raw_data['layer']}
            site_info['devices'].append(device_info)
        except Exception as e:
            message = 'Could not fetch NSM info for {}:  {}'.format(device, e)
            logging.error(message)
    return site_info

def write_to_ddb(results,dx_devices_and_sites,region_devices):
    site_table = ddb.get_ddb_table('dx_site_table')
    device_port_table= ddb.get_ddb_table('dx_device_port_table')
    region_table = ddb.get_ddb_table('dx_region_table')
    for region in region_devices:
        ddb.put_item_to_table(region_table, region)
    for site in dx_devices_and_sites:
        ddb.put_item_to_table(site_table, site)
    for result in results:
        for  device in result.get()['devices']:
            response = ddb.put_item_to_table(device_port_table,{'device': device['name'], 'ports' : device['ports']})
            if response:
                logging.info("Router: {} - Saved to DDB table".format(device['name']))
            else:
                logging.error("Router: {} - Failed to save to DDB table".format(device['name']))

def write_vc_cor_to_ddb(vc_cor_table_scan):
    all_vc_ports = list()
    device_port_table= ddb.get_ddb_table('dx_device_port_table')

    for device in vc_cor_table_scan:
        interfaces = dict()
        device_raw_json = nsm.get_raw_device(device['Name'])
        portmodel.build_device_port_availability_map(interfaces,device['Name'],device_raw_json)
        all_vc_ports.append({'device':device['Name'],'ports':interfaces})

    for device in all_vc_ports:
        response = ddb.put_item_to_table(device_port_table,device)
        if response:
            logging.info("Router: {} - Saved to DDB table".format(device['device']))
        else:
            logging.error("Router: {} - Failed to save to DDB table".format(device['device']))

#def spc_ip_table_update():
#	device_pattern = 'name:/.*br-spc.*ced.*t1.*/'
#	spc_devices = {}
#	
#	for region in REGIONS:
#		devices = get_devices_from_nsm(device_pattern, region, ['OPERATIONAL'])
#		if devices:
#			spc_devices[region] = devices
#	
#	regions_bricks = {}
#	
#	for region in spc_devices.keys():
#		regions_bricks[region] = {}
#		for device in spc_devices[region]:
#			brick_num = device.split('-f1-')[1].split('-ced')[0]
#			border_pop = device.split('-')[0]
#			border_pop_list = []
#			if not brick_num in regions_bricks[region]:
#				regions_bricks[region][brick_num] = []
#				regions_bricks[region][brick_num].append(border_pop)
#			else:
#				if not border_pop in regions_bricks[region][brick_num]:
#					regions_bricks[region][brick_num].append(border_pop)
#	
#	region_brick_block = {}
#	for region in regions_bricks.keys():
#		region_brick_block[region] = {}
#		for brick in regions_bricks[region]:
#			region_brick_block[region]['pop'] = regions_bricks[region][brick]
#			region_brick_block[region][brick] = []
#			for pop in regions_bricks[region][brick]:
#				brick_ips = telesto.get_free_ced_cidr(pop,int(brick.split('b')[1]))
#				brick_ips_str = []
#				for brick_ip in brick_ips:
#					brick_ips_str.append(str(brick_ip))
#				temp_holder = []
#				if not region_brick_block[region][brick]:
#					region_brick_block[region][brick] = brick_ips_str
#					temp_holder = brick_ips_str
#				else:
#					for brick_ip in brick_ips_str:
#						if brick_ip in region_brick_block[region][brick]:
#							temp_holder.append(brick_ip)
#				region_brick_block[region][brick] = temp_holder
#
#	region_brick_block = {}
#	for region in regions_bricks.keys():
#		region_brick_block[region] = {}
#		region_brick_block[region]['pop'] = []
#		region_brick_block[region]['brick_num'] = []
#		brick_num = []
#		for brick in regions_bricks[region]:
#			region_brick_block[region]['pop'] += regions_bricks[region][brick]
#			brick_num.append(brick)
#			region_brick_block[region]['brick_num'] = list(set(brick_num))
#			region_brick_block[region]['pop'] = list(set(region_brick_block[region]['pop']))
#			region_brick_block[region][brick] = []
#			for pop in regions_bricks[region][brick]:
#				brick_ips = telesto.get_free_ced_cidr(pop,int(brick.split('b')[1]))
#				brick_ips_str = {}
#				for brick_ip in brick_ips:
#					brick_ips_str[str(brick_ip)] = 'Available'
#				temp_holder = {}
#				if not region_brick_block[region][brick]:
#					region_brick_block[region][brick] = brick_ips_str
#					temp_holder = brick_ips_str
#				else:
#					for brick_ip in brick_ips_str:
#						if brick_ip in region_brick_block[region][brick]:
#							temp_holder[brick_ip] = 'Available'
#				region_brick_block[region][brick] = temp_holder
#	
#	final_dict_list = []
#	for region in region_brick_block.keys():
#		final_dict = {}
#		final_dict['region'] = region
#		for brick in region_brick_block[region].keys():
#			final_dict[brick] = region_brick_block[region][brick]
#		final_dict_list.append(final_dict)
#	
#	ip_table = ddb.get_ddb_table('spc_ip_table')
#	
#	scanned_table = ddb.scan_full_table(ip_table)
#
#	check_region = 0
#	for region in final_dict_list:
#		for ddb_region in scanned_table:
#			if region['region'] == ddb_region['region'] and sorted(region['brick_num']) == sorted(ddb_region['brick_num']):
#				for brick in region['brick_num']:
#					for brick_ip in region[brick].keys():
#						if ddb_region[brick].get(brick_ip) and region[brick].get(brick_ip):
#							region[brick][brick_ip] = ddb_region[brick].get(brick_ip)
#	
#	for item in final_dict_list:
#		ddb.put_item_to_table(ip_table, item)

def main():
    pool = Pool(16)
    results =[]
    region_devices=get_jb_dx_devices_region()
    dx_devices_and_sites = get_jb_dx_devices_sites()
    for dx_devices_and_site in dx_devices_and_sites:
        results.append(pool.apply_async(get_site_info, args = (dx_devices_and_site,)))
    write_to_ddb(results,dx_devices_and_sites,region_devices)
    VC_COR_TABLE = ddb.get_ddb_table('vc_cor_table')
    vc_cor_table_scan = ddb.scan_full_table(VC_COR_TABLE)
    write_vc_cor_to_ddb(vc_cor_table_scan)
#   spc_ip_table_update()

if __name__ == '__main__':
    main()
