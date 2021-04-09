#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import sys
import argparse
import os
import logging
import time
import re
from multiprocessing import Pool

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

from isd_tools_dev.modules import ddb
from dxd_tools_dev.modules import nsm
from dxd_tools_dev.modules import hercules
from dxd_tools_dev.datastore import ddb as ddb_dxd
from dxd_tools_dev.modules import jukebox

MS_DX_DDB_RW = 'com.amazon.credentials.isengard.749865518066.user/dx_tools_ddb_rw'
DX_DEVICES_TABLE = 'dx_devices_table'
VC_COR_TABLE = 'vc_cor_table'
MX_FPC_SCB_TABLE = 'mx_fpc_scb_table'
TC_POP_BORDER_CAPACITY_TABLE = 'tc_pop_border_capacity_table'
VC_COR_BGP_RSVP_PRESTAGE_TABLE = 'vc_cor_bgp_rsvp_prestage_table'
AWS_REGION = 'us-east-2'

links = True

MX480_FPC_SLOTS = ['FPC 0','FPC 1','FPC 2','FPC 3','FPC 4','FPC 5']
MX960_FPC_SLOTS = ['FPC 0','FPC 1','FPC 2','FPC 3','FPC 4','FPC 5','FPC 7','FPC 8','FPC 9','FPC 10','FPC 11']

def initialize_globals(device_regex = "name:/.*-vc-(bar|car|cir|agg|fab|edg|cas|dar|crr|cor)-.*/"):
    logging.info('Start Time: {}'.format(time.strftime("%c")))
    global global_dx_device_table
    global global_vc_cor_table
    global global_mx_fpc_scb_table
    global global_tc_pop_border_capacity_table
    global global_vc_cor_bgp_rsvp_prestage_table

    global global_dx_device_table_scan
    global global_vc_cor_table_scan
    global global_mx_fpc_scb_table_scan
    global global_tc_pop_border_capacity_table_scan

    global device_list
    global decommissioned_devices_all

    jukebox_device_states = ["in-service","configured"]
    jukebox_devices = jukebox.get_all_devices_in_jukebox(device_states=jukebox_device_states)
    jukebox_devices_list = [j for i in jukebox_devices for j in i['devices']]

    device_nsm_list = nsm.get_devices_from_nsm(device_regex)

    all_dx_devices = jukebox_devices_list + device_nsm_list
    device_list = sorted(set(all_dx_devices))

    decommissioned_devices_all = nsm.get_devices_from_nsm(device_regex, state = 'DECOMMISSIONED')

    global_dx_device_table = ddb.get_ddb_table(AWS_REGION, MS_DX_DDB_RW, DX_DEVICES_TABLE)
    global_mx_fpc_scb_table = ddb.get_ddb_table(AWS_REGION, MS_DX_DDB_RW, MX_FPC_SCB_TABLE)
    global_vc_cor_table = ddb.get_ddb_table(AWS_REGION, MS_DX_DDB_RW, VC_COR_TABLE)
    global_tc_pop_border_capacity_table = ddb.get_ddb_table(AWS_REGION, MS_DX_DDB_RW, TC_POP_BORDER_CAPACITY_TABLE)
    global_vc_cor_bgp_rsvp_prestage_table = ddb.get_ddb_table(AWS_REGION, MS_DX_DDB_RW, VC_COR_BGP_RSVP_PRESTAGE_TABLE)

    global_dx_device_table_scan = ddb_dxd.scan_full_table(global_dx_device_table)
    global_mx_fpc_scb_table_scan = ddb_dxd.scan_full_table(global_mx_fpc_scb_table)
    global_vc_cor_table_scan = ddb_dxd.scan_full_table(global_vc_cor_table)

def save_dx_device_ddb():
    logging.info("Starting save_dx_device_ddb, Fetching device info from NSM")
    devices_data = list()

    pool = Pool(8)

    for device in device_list:
        devices_data.append(pool.apply_async(nsm.get_device_detail_from_nsm, args = (device,links,)))

    for device in devices_data:
        try:
            if 'vc-cor' in device.get()['Name']:
                if device.get()['Hardware']['Chassis'][0] != 'None':
                    vc_cor_response = ddb.put_item_to_table(global_vc_cor_table,device.get())
                    response = ddb.put_item_to_table(global_dx_device_table,device.get())
            elif re.match('.*-vc-(bar|car|cir|agg|fab|edg|dar)-.*', device.get()['Name']):
                if device.get()['Hardware']['Chassis'][0] != 'None':
                    response = ddb.put_item_to_table(global_dx_device_table,device.get())
            else:
                response = ddb.put_item_to_table(global_dx_device_table,device.get())
        except:
            pass

        try:
            if response or vc_cor_response:
                logging.info("Router: {} - Saved to DDB table".format(device.get()['Name']))
            else:
                logging.error("Router: {} - Failed to save to DDB table".format(device.get()['Name']))
        except TypeError as error:
            logging.error("TypeError - Router {} does not have record. Not saved to DDB table".format(device.get()))

def save_mx_480_960_status():
    logging.info("Starting save_mx_480_960_status ...")
    device_hardware_dict = dict()
    device_fpc_status_list = list()

    pattern_name = '.*-vc-(car|edg|agg)-.*'
    pattern_model = 'mx(480|960)'

    for device in global_dx_device_table_scan:
        if re.match(pattern_name,device['Name'].lower()) and re.match(pattern_model,device['Model'].lower()):
            device_hardware_dict.update({device['Name']:device['Hardware']})

    for device in device_hardware_dict:
        if device_hardware_dict[device]['Chassis'][0] == 'MX480':
            device_fpc_status_dict = dict()
            available_fpcs = list(set(MX480_FPC_SLOTS) - set(list(device_hardware_dict[device]['FPC'].keys())))
            device_fpc_status_dict.update({'Name':device,'Chassis':device_hardware_dict[device]['Chassis'],'Occupied FPC Slots':list(device_hardware_dict[device]['FPC'].keys()),'Available FPC Slots':available_fpcs,'SCB':device_hardware_dict[device]['SCB']})
        elif device_hardware_dict[device]['Chassis'][0] == 'MX960':
            device_fpc_status_dict = dict()
            available_fpcs = list(set(MX960_FPC_SLOTS) - set(list(device_hardware_dict[device]['FPC'].keys())))
            device_fpc_status_dict.update({'Name':device,'Chassis':device_hardware_dict[device]['Chassis'],'Occupied FPC Slots':list(device_hardware_dict[device]['FPC'].keys()),'Available FPC Slots':available_fpcs,'SCB':device_hardware_dict[device]['SCB']})
        device_fpc_status_list.append(device_fpc_status_dict)

    for device in device_fpc_status_list:
        response = ddb.put_item_to_table(global_mx_fpc_scb_table,device)
        try:
            if response:
                logging.info("Router: {} - Saved to DDB table".format(device['Name']))
            else:
                logging.error("Router: {} - Failed to save to DDB table".format(device['Name']))
        except TypeError as error:
            logging.error("TypeError - Router {} does not have record. Not saved to DDB table".format(device))

def save_car_dar_border_bandwidth():
    logging.info("Starting save_car_dar_border_bandwidth ...")
    devices_bandwidth_list = list()
    site_list = list()
    sites = list()
    unique_sites = ()
    pattern_name = '.*-vc-(car|dar)-.*'
    pattern_desc = '.*-(br-tra|vc-cor)-.*'

    for device in global_dx_device_table_scan:
        devices_bandwidth_dict = dict()
        device_bandwidth_list = list()
        if re.match(pattern_name,device['Name'].lower()):
            device_border_bandwidth = int()
            try:
                for interface in device['Interfaces']:
                    device_bandwidth_dict = dict()
                    if interface['Class'] == 'aggregate' and re.match(pattern_desc,interface['Description'].lower()):
                        device_border_bandwidth += int(interface['Bandwidth_Mbps'])/1000
                        device_bandwidth_dict.update({'Interface':interface['Name'],'bandwidth':int(int(interface['Bandwidth_Mbps'])/1000),'description':interface['Description']})
                        device_bandwidth_list.append(device_bandwidth_dict)
                devices_bandwidth_dict.update({'name':device['Name'],'bandwidth':device_border_bandwidth,'interfaces':device_bandwidth_list})
                devices_bandwidth_list.append(devices_bandwidth_dict)
            except KeyError as error:
                logging.error('Device {} does not have {} Key'.format(device['Name'], error))

    for site in devices_bandwidth_list:
        sites.append(site['name'].split('-')[0])

    unique_sites = list(set(sites))

    for site in unique_sites:
        site_devices_bandwidth_list = list()
        total_site_bandwidth = int()
        site_dict = dict()
        for bandwidth in devices_bandwidth_list:
            site_device_bandwidth_dict = dict()
            if site == bandwidth['name'].split('-')[0]:
                total_site_bandwidth += bandwidth['bandwidth']
                site_device_bandwidth_dict.update({'Name':bandwidth['name'],'Bandwidth_Gbps':int(bandwidth['bandwidth']),'interfaces':bandwidth['interfaces']})
                site_devices_bandwidth_list.append(site_device_bandwidth_dict)
        site_dict.update({'Site':site.upper(),'Site_Bandwidth_Gbps':int(total_site_bandwidth),'Devices_Bandwidth_Gbps':site_devices_bandwidth_list})
        site_list.append(site_dict)

    logging.info("Saving info to TC_POP_BORDER_CAPACITY_TABLE")

    for site in site_list:
        response = ddb.put_item_to_table(global_tc_pop_border_capacity_table,site)
        try:
            if response:
                logging.info("Site: {} - Saved to DDB table".format(site['Site']))
            else:
                logging.error("Site: {} - Failed to save to DDB table".format(site['Site']))
        except TypeError as error:
            logging.error("TypeError - Site {} does not have record. Not saved to DDB table".format(site))

def delete_decommissioned_devices():
    logging.info("Starting delete_decommissioned_devices ...")
    decommissioned_devices_strict = list()

    for decommissioned_device in decommissioned_devices_all:
        if decommissioned_device not in device_list:
            decommissioned_devices_strict.append(decommissioned_device)

    for device in global_dx_device_table_scan:
        if device['Name'] in decommissioned_devices_strict:
            item_to_be_deleted = dict()
            item_to_be_deleted.update({'Name':device['Name']})
            response = ddb_dxd.delete_item_from_table(global_dx_device_table,item_to_be_deleted)
            try:
                if response:
                    logging.info("Decommissioned device: {} - deleted from to DDB table".format(device['Name']))
                else:
                    logging.error("Decommissioned device: {} - Failed to delete from DDB table".format(device['Name']))
            except:
                logging.error("Exception: {}".format(sys.exc_info()))

    for device in global_mx_fpc_scb_table_scan:
        if device['Name'] in decommissioned_devices_strict:
            item_to_be_deleted = dict()
            item_to_be_deleted.update({'Name':device['Name']})
            response = ddb_dxd.delete_item_from_table(global_dx_device_table,item_to_be_deleted)
            try:
                if response:
                    logging.info("Decommissioned device: {} - deleted from to DDB table".format(device['Name']))
                else:
                    logging.error("Decommissioned device: {} - Failed to delete from DDB table".format(device['Name']))
            except:
                logging.error("Exception: {}".format(sys.exc_info()))

    for device in global_vc_cor_table_scan:
        if device['Name'] in decommissioned_devices_strict:
            item_to_be_deleted = dict()
            item_to_be_deleted.update({'Name':device['Name']})
            response = ddb_dxd.delete_item_from_table(global_dx_device_table,item_to_be_deleted)
            try:
                if response:
                    logging.info("Decommissioned device: {} - deleted from to DDB table".format(device['Name']))
                else:
                    logging.error("Decommissioned device: {} - Failed to delete from DDB table".format(device['Name']))
            except:
                logging.error("Exception: {}".format(sys.exc_info()))

def save_vc_cor_bgp_rsvp_prestage():
    logging.info("Starting save_vc_cor_bgp_rsvp_prestage ...")
    REGIONS = ['iad', 'pdx', 'cmh', 'syd', 'hkg', 'nrt', 'sfo', 'sin', 'arn', 'bjs', 'fra', 'bom', 'dub', 'lhr', 'yul', 'kix', 'cdg', 'bah', 'zhy', 'icn', 'gru', 'cpt', 'mxp']
    for region in REGIONS:
        logging.info("Fetching vc-cors from {} hercules stack".format(region.upper()))
        vc_cor_in_region = hercules.get_vc_cor_in_region(region)
        if vc_cor_in_region:
            vc_cor_border_bgp_lsp_neigbors = list()
            all_vc_cor_border_bgp_lsp_neigbors = list()

            for site in vc_cor_in_region:
                for device in site['vc_cor_devices']:
                    all_vc_cor_border_bgp_lsp_neigbors.append(hercules.get_vc_cor_border_bgp_lsp(device))

            pattern = '.*(IBGP-VCCOR-VCCOR|RR-VCCOR-CLIENT|IBGP-VCCOR|IBGP-BIB-VCCOR|IBGP-TRA-VCCOR|IBGP-SBC-VCCOR|IBGP-UBQ-VCCOR|IBGP-ENTRA-VCCOR|IBGP-GCT-VCCOR|RR-IBGP-VCCOR-CLIENT) neighbor.*|.*label-switched-path.*-VC-.*to .*'

            vc_cor_prestage_details = list()
            for site in vc_cor_in_region:
                for device in site['vc_cor_devices']:
                    vc_cor_prestage_details.append({'Name':device,'site':device.split('-')[0],'metro':device.split('-')[0][:3],'bgp_fully_prestaged':'yes','rsvp_fully_prestaged':'yes','border_bgp_prestage': {}})

            border_detailed_info = list()
            neighbors_log = list()
            for device in all_vc_cor_border_bgp_lsp_neigbors:
                for neighbor in device['border_bgp_neighbors']:
                    if neighbor not in neighbors_log:
                        neighbors_log.append(neighbor)
                        config_lines = hercules.get_config_matching_pattern(neighbor,pattern)
                        bgp = list()
                        rsvp = list()
                        border_dict = dict()
                        for line in config_lines:
                            if 'description' in line:
                                bgp.append(line.split(' ')[-1])
                            if 'label-switched-path' in line:
                                rsvp.append(line.split(' ')[6])
                        border_dict.update({'Name':neighbor,'bgp_prestaged':bgp,'site':neighbor.split('-')[0],'rsvp_prestaged':rsvp})
                        border_detailed_info.append(border_dict)

            border_bgp_devices = dict()
            for device in all_vc_cor_border_bgp_lsp_neigbors:
                border_site_devices = dict()
                for neighbor in device['border_bgp_neighbors']:
                    if device['name'].split('-')[0] == neighbor.split('-')[0]:
                        border_site_devices.update({neighbor:'no'})
                border_bgp_devices.update({device['name']:border_site_devices})

            for i,x in enumerate(vc_cor_prestage_details):
                for j in border_bgp_devices:
                    if x['Name'] == j:
                        vc_cor_prestage_details[i].update({'border_bgp_prestage':border_bgp_devices[j]})

            for i,x in enumerate(vc_cor_prestage_details):
                lsp_prestaged = dict()
                for j in x['border_bgp_prestage']:
                    if 'rrr' not in j and 'gct' not in j and 'lle' not in j:
                        lsp_1 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR1'
                        lsp_2 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR2'
                        lsp_3 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR3'
                        lsp_4 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR4'
                        lsp_5 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR5'
                        lsp_6 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR6'
                        lsp_7 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR7'
                        lsp_8 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR8'
                        lsp_prestaged[lsp_1] = 'no'
                        lsp_prestaged[lsp_2] = 'no'
                        lsp_prestaged[lsp_3] = 'no'
                        lsp_prestaged[lsp_4] = 'no'
                        lsp_prestaged[lsp_5] = 'no'
                        lsp_prestaged[lsp_6] = 'no'
                        lsp_prestaged[lsp_7] = 'no'
                        lsp_prestaged[lsp_8] = 'no'
                    if 'rrr' not in j and 'gct' in j:
                        lsp_1 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR1'
                        lsp_2 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR2'
                        lsp_3 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR3'
                        lsp_4 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR4'
                        lsp_5 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR5'
                        lsp_6 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR6'
                        lsp_7 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR7'
                        lsp_8 = 'GRUMPYCAT_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR8'
                        lsp_prestaged[lsp_1] = 'no'
                        lsp_prestaged[lsp_2] = 'no'
                        lsp_prestaged[lsp_3] = 'no'
                        lsp_prestaged[lsp_4] = 'no'
                        lsp_prestaged[lsp_5] = 'no'
                        lsp_prestaged[lsp_6] = 'no'
                        lsp_prestaged[lsp_7] = 'no'
                        lsp_prestaged[lsp_8] = 'no'
                    if 'lle' in j:
                        lsp_1 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR1'
                        lsp_2 = 'INTRACLUSTER_'+ j.upper() + '_TO_' + x['Name'].upper() + '_COLOR2'
                        lsp_prestaged[lsp_1] = 'no'
                        lsp_prestaged[lsp_2] = 'no'
                vc_cor_prestage_details[i].update({'border_rsvp_prestage':lsp_prestaged})

            for i,x in enumerate(vc_cor_prestage_details):
                for j in border_detailed_info:
                    if j['site'] == x['site'] and x['Name'] in j['bgp_prestaged']:
                        vc_cor_prestage_details[i]['border_bgp_prestage'].update({j['Name']:'yes'})

            for i,x in enumerate(vc_cor_prestage_details):
                for j in border_detailed_info:
                    for k in j['rsvp_prestaged']:
                        name = '.*TO_' + x['Name'].upper() + '.*_'
                        if re.match(name,k):
                            vc_cor_prestage_details[i]['border_rsvp_prestage'].update({k:'yes'})

            for i in vc_cor_prestage_details:
                for j in i['border_bgp_prestage']:
                    if i['border_bgp_prestage'].get(j) == 'no':
                        i.update({'bgp_fully_prestaged':'no'})
                        break

            for i in vc_cor_prestage_details:
                for j in i['border_rsvp_prestage']:
                    if i['border_rsvp_prestage'].get(j) == 'no':
                        i.update({'rsvp_fully_prestaged':'no'})
                        break

            for device in vc_cor_prestage_details:
                response = ddb.put_item_to_table(global_vc_cor_bgp_rsvp_prestage_table,device)
                try:
                    if response:
                        logging.info("Router: {} - Saved to DDB table".format(device['Name']))
                    else:
                        logging.error("Router: {} - Failed to save to DDB table".format(device['Name']))
                except TypeError as error:
                    logging.error("TypeError - Router {} does not have record. Not saved to DDB table".format(device))

    logging.info('Script has ended at: {}'.format(time.strftime("%c")))

def main():
    initialize_globals()
    delete_decommissioned_devices()
    save_dx_device_ddb()
    save_mx_480_960_status()
    save_car_dar_border_bandwidth()
    save_vc_cor_bgp_rsvp_prestage()

if __name__ == '__main__':
    main()
