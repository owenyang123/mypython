#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import maestro_db, equinix_api
from dxd_tools_dev.datastore import ddb
import sys
import argparse
import re
import collections
import os
from collections import defaultdict
import pandas as pd


def account_info(devices_interfaces_dict,region):
    print("INFO: Getting account details please share account details with only the appropriate teams")    

    maestro_dict = {}
    for device in devices_interfaces_dict.keys():
        output_list = []
        query_list = []
        First = True
        for interface in devices_interfaces_dict[device]["INTERFACES"].keys():
            if First:
                query_list.append("ppr.interface_name = '"+interface+"' ")
                First = False
            else:
                query_list.append("or ppr.interface_name = '"+interface+"' ")
        query = "select d.hostname, ppr.interface_name, pp.available_at, pc.obfuscated_id, pc.owner_account, pc.state from physical_port_reservations ppr join physical_ports pp on pp.physical_port_reservation_id=ppr.id join physical_connections pc on pc.physical_port_id=pp.id join devices d on d.id=ppr.device_id where d.hostname like '"+device+"%' and ("+"".join(query_list)+") order by pp.available_at asc;\n"
        f =  maestro_db.query_Maestro(region,query)

        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")])
        for data_list in output_list[1:]:
            if "." in data_list[1]:
                maestro_dict[data_list[1].split(".")[0]] = {}
                maestro_dict[data_list[1].split(".")[0]]["INTERFACES"] = {}
            else:
                maestro_dict[data_list[1]] = {}
                maestro_dict[data_list[1]]["INTERFACES"] = {}       

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                maestro_dict[data_list[1].split(".")[0]]["INTERFACES"][data_list[2]]= {}
                maestro_dict[data_list[1].split(".")[0]]["INTERFACES"][data_list[2]]["Connection_ID"] = data_list[4]
                maestro_dict[data_list[1].split(".")[0]]["INTERFACES"][data_list[2]]["Account_number"] = data_list[5]
                maestro_dict[data_list[1].split(".")[0]]["INTERFACES"][data_list[2]]["Status_IN_DB"] = data_list[6]

            else:
                maestro_dict[data_list[1]]["INTERFACES"][data_list[2]]= {}
                maestro_dict[data_list[1]]["INTERFACES"][data_list[2]]["Connection_ID"] = data_list[4]
                maestro_dict[data_list[1]]["INTERFACES"][data_list[2]]["Account_number"] = data_list[5]
                maestro_dict[data_list[1]]["INTERFACES"][data_list[2]]["Status_IN_DB"] = data_list[6]

    for device in devices_interfaces_dict.keys():
        for interface in devices_interfaces_dict[device]['INTERFACES'].keys():
            try: 
                devices_interfaces_dict[device]['INTERFACES'][interface]["Connection_ID"] = maestro_dict[device]['INTERFACES'][interface]["Connection_ID"]
                devices_interfaces_dict[device]['INTERFACES'][interface]["Account_number"] = maestro_dict[device]['INTERFACES'][interface]["Account_number"]
                devices_interfaces_dict[device]['INTERFACES'][interface]["Status_IN_DB"] = maestro_dict[device]['INTERFACES'][interface]["Status_IN_DB"]

            except:
                devices_interfaces_dict[device]['INTERFACES'][interface]['Connection_ID'] = "N_A"
                devices_interfaces_dict[device]['INTERFACES'][interface]['Account_number'] = "N_A"
                devices_interfaces_dict[device]['INTERFACES'][interface]['Status_IN_DB'] = "N_A"
                pass
    return devices_interfaces_dict



def read_devices(csv):


    dint_dict = {}
    df = pd.read_csv(csv)
    df = df.sort_values('device')
    df.to_csv(csv, index=False)
    df = pd.read_csv(csv)
    csv_dict = df.to_dict()


    for item1 in csv_dict['device'].items():
        if '.' in item1[1]:
            device = item1[1].split('.')[0]
        else:
            device = item1[1]
        dint_dict[device] = {}
        dint_dict[device]["INTERFACES"] = {}

    for i in range(0, len(df)):
        if '.' in csv_dict['device'][i]:
            device = csv_dict['device'][i].split('.')[0]
        else:
            device = csv_dict['device'][i]
        dint_dict[device]["INTERFACES"][csv_dict['interfaceName'][i]] = {}
        dint_dict[device]["INTERFACES"][csv_dict['interfaceName'][i]]["Patch_Panel"] = csv_dict['patchPanel'][i]
        dint_dict[device]["INTERFACES"][csv_dict['interfaceName'][i]]["Colo"] = csv_dict['directConnectLocationCode'][i]
        dint_dict[device]["INTERFACES"][csv_dict['interfaceName'][i]]["sub_Colo"] = csv_dict['directConnectSubLocationCode'][i]
        dint_dict[device]["INTERFACES"][csv_dict['interfaceName'][i]]["port"] = str(csv_dict['port'][i])

    return dint_dict



def audit_equinix(devices_interfaces_dict,region_equinix):
    print("INFO: doing audit for Equinix if they exist")

    token = equinix_api.get_equinix_token(region_equinix)

    for device in devices_interfaces_dict.keys():
        for interface in devices_interfaces_dict[device]['INTERFACES'].keys():
            if 'eq' in devices_interfaces_dict[device]['INTERFACES'][interface]['Colo'].lower():
                if 'wbe' in str(devices_interfaces_dict[device]['INTERFACES'][interface]['sub_Colo']).lower():
                    devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Site'] = 'NO'
                    devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Patch_Panel'] = 'N_A'
                    devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = 'N_A'

                else:
                    available_ports = False
                    equnix_response = False
                    used_ports = []
                    devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Site'] = 'Yes'

                    equnix_response = equinix_api.get_patch_panel_details(token, devices_interfaces_dict[device]['INTERFACES'][interface]['Patch_Panel'])
                    try:
                        available_ports = [str(i) for i in equnix_response['availablePorts']]
                        devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Patch_Panel'] = 'exists'
                    except:
                        try:
                            devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Patch_Panel'] = equnix_response[0]['additionalInfo'][0]['reason']
                        except:
                            devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Patch_Panel'] = "WRONG PATCH PANEL NAME"
                            pass

                    if available_ports:
                        try:
                            for used_Port_dict in equnix_response['usedPortsDetails']:
                                used_ports.append(str(used_Port_dict['portNumber']))
                        except:
                            pass

                    if not available_ports:
                        devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Patch Panel Error Consider updating DXDB with the right info for this device by working with DCO"

                    elif len(devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split("/")) > 1:
                        for port in devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split("/"):
                            if port.strip() in available_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Free"
                                break
                            elif port.strip() in used_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Occupied"
                                break
                            else:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port Doesnt exist manual audit is required"

                    elif len(devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split("+")) > 1:
                        for port in devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split("+"):
                            if port.strip() in available_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Free"
                                break
                            elif port.strip() in used_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Occupied"
                                break
                            else:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port Doesnt exist manual audit is required"

                    elif len(devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split("-")) > 1:
                        for port in devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split("-"):
                            if port.strip() in available_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Free"
                                break
                            elif port.strip() in used_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Occupied"
                                break
                            else:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port Doesnt exist manual audit is required"

                    elif len(devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split()) < 2:
                        for port in devices_interfaces_dict[device]['INTERFACES'][interface]["port"].split():
                            if port.strip() in available_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Free"
                                break
                            elif port.strip() in used_ports:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port is Occupied"
                                break
                            else:
                                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port Doesnt exist manual audit is required"
                    else:
                        devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = "Port Doesnt exist manual audit is required"

            else:
                devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Site'] = 'NO'
                devices_interfaces_dict[device]['INTERFACES'][interface]['Equinix_Patch_Panel'] = 'N_A'
                devices_interfaces_dict[device]['INTERFACES'][interface]['port_status_in_Equinix'] = 'N_A'
    return devices_interfaces_dict


def audit_config(devices_interfaces_dict):
    table = ddb.get_ddb_table('dx_devices_table')
    for device in devices_interfaces_dict.keys():
        print("INFO: Getting config for "+device)

        try:
            info = ddb.get_device_from_table(table,'Name',device)
        except:

            log_error = "Could not get interface info from DB of {}".format(device)
            logging.error(log_error)
            sys.exit()

        if 'v4' in device or 'v5' in device:
            try:
                config = os.popen('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file running-config'.format(device)).read().splitlines()
            except:
                log_error = "Could not get config info from Hercules of {}".format(device1)
                logging.error(log_error)
                sys.exit()


            for interface in devices_interfaces_dict[device]["INTERFACES"].keys():
                for i in range(len(info['Interfaces'])):
                    cisco_interface_split = interface.split('eth')
                    cisco_interface_split[0] = 'Ethernet'
                    cisco_interface = "".join(cisco_interface_split)
                    if info['Interfaces'][i]['Name'] == cisco_interface:
                        devices_interfaces_dict[device]["INTERFACES"][interface]['oper-status'] = info['Interfaces'][i]['Status']

                interfaces_config = list()
                config_check = False
                admin_status = False
                config_on_interface = False
                if "cas" in device:
                    for i in range(0,len(config)):
                        if config_check:
                            break
                        elif config[i] == 'interface '+cisco_interface:
                            for k in range(i+1, len(config)):
                                if 'interface' in config[k]:
                                    config_check = True
                                    break
                                elif 'description' in config[k]:
                                    devices_interfaces_dict[device]["INTERFACES"][interface]["CONFIG"] = "WARNING THERE's CONFIG on THE INTERFACE"
                                    config_on_interface = True

                                elif  config[k] == 'shutdown':
                                    devices_interfaces_dict[device]["INTERFACES"][interface]["admin-status"] = "DOWN"
                                    devices_interfaces_dict[device]["INTERFACES"][interface]["CONFIG"] = "WARNING THERE's CONFIG on THE INTERFACE"
                                    admin_status = True
                                    config_on_interface = True


                                else:
                                    continue
                        else:
                            continue
                if not admin_status and not config_on_interface:
                    devices_interfaces_dict[device]["INTERFACES"][interface]["admin-status"] = "UP"
                    devices_interfaces_dict[device]["INTERFACES"][interface]["CONFIG"] = "NO_Config"

                elif not admin_status:
                    devices_interfaces_dict[device]["INTERFACES"][interface]["admin-status"] = "UP"
        else:

            try:
                config = os.popen('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file set-config '.format(device)).read().splitlines()
            except:

                log_error = "Could not get config info from Hercules of {}".format(device1)
                logging.error(log_error)
                sys.exit()
            for interface in devices_interfaces_dict[device]["INTERFACES"].keys():
                for i in range(len(info['Interfaces'])):
                    if info['Interfaces'][i]['Name'] == interface:
                        devices_interfaces_dict[device]["INTERFACES"][interface]["oper-status"] = info['Interfaces'][i]['Status']
                interfaces_config = list()
                if "cas" in device:
                    for config_line in config:
                        if ("set interfaces "+interface+" description") in config_line or ("set interfaces "+interface+" disable") in config_line:
                            interfaces_config.append(config_line)
                else:
                    for config_line in config:
                        if ("set interfaces "+interface+" ") in config_line:
                            interfaces_config.append(config_line)

                if interfaces_config:
                    if ('set interfaces '+interface+' disable') in interfaces_config:
                        devices_interfaces_dict[device]["INTERFACES"][interface]["CONFIG"] = "WARNING THERE's CONFIG on THE INTERFACE"
                        devices_interfaces_dict[device]["INTERFACES"][interface]["admin-status"] = "DOWN"
                    else:
                        devices_interfaces_dict[device]["INTERFACES"][interface]["admin-status"] = "UP"
                        devices_interfaces_dict[device]["INTERFACES"][interface]["CONFIG"] = "WARNING THERE's CONFIG on THE INTERFACE"
                else:
                    devices_interfaces_dict[device]["INTERFACES"][interface]["admin-status"] = "UP"
                    devices_interfaces_dict[device]["INTERFACES"][interface]["CONFIG"] = "NO_Config"
    return devices_interfaces_dict



def write_csv(interface_of_devices_dict,csv,region):
    print("INFO: writing the csv file")    
    with open(csv) as csv_file:
        csv_to_list = list()
        for line in csv_file.read().splitlines():
            csv_to_list.append(line.split(","))
    csv_to_list[0].append('device')
    csv_to_list[0].append('Interface')
    csv_to_list[0].append('admin-status')
    csv_to_list[0].append('oper-status')
    csv_to_list[0].append('Config')
    csv_to_list[0].append('Equinix Site')
    csv_to_list[0].append('Equinix Patch Panel')
    csv_to_list[0].append('port status in Equinix')
    csv_to_list[0].append('Connection_ID')
    csv_to_list[0].append('Account number')
    csv_to_list[0].append('Port Status in Database Available Taken/Deleted Released')
    csv_to_list[0].append('Release Date')
    csv_to_list[0].append('Status Occupied or Free')
    csv_to_list[0].append('CID')
    csv_to_list[0].append('Notes')

    row = 1
    for device in interface_of_devices_dict.keys():
        print("INFO: writing csv data for "+device)
        for interface in interface_of_devices_dict[device]["INTERFACES"].keys():
            csv_to_list[row].append(device)
            csv_to_list[row].append(interface)
            csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]['admin-status'])
            csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]['oper-status'])
            csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]['CONFIG'])
            csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]['Equinix_Site'])
            csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]['Equinix_Patch_Panel'])
            csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]['port_status_in_Equinix'])

            if region:
                csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]["Connection_ID"])
                csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]["Account_number"])
                csv_to_list[row].append(interface_of_devices_dict[device]["INTERFACES"][interface]["Status_IN_DB"])
            row += 1
    outlist = []
    for row in csv_to_list:
        outlist.append(",".join(row))
    outcsv = "\n".join(outlist)
    with open("outputcsv.csv",'w') as f:
        f.write(outcsv)

    writer = pd.ExcelWriter('output.xlsx')
    df = pd.read_csv('outputcsv.csv')
    df = df.fillna(' ')
    df = df.astype(str)
    df.to_excel(writer, 'output', index=False)
    writer.save()
    os.remove('outputcsv.csv')




def port_re():
    parser = argparse.ArgumentParser(description='port_re script will audit the ports in the input csv file by running show commands in devices...output will be named outputcsv.csv \n scp this file to your machines to see the results ')
    parser.add_argument('--interface_csv', help='csv file with device and interfaces')
    parser.add_argument('--account_info_region', help='Optional specify the region where account info is needed')
    parser.add_argument('--region_equinix', help='required specify the region of the devices such iad or pdx...')
    args = parser.parse_args()

    if args.interface_csv and args.region_equinix and not args.account_info_region :
        region = False
        csv = args.interface_csv
        write_csv(audit_config(audit_equinix(read_devices(csv),args.region_equinix)),csv,region)

    elif args.interface_csv and args.region_equinix and args.account_info_region:
        region = args.account_info_region
        csv = args.interface_csv
        write_csv(audit_config(account_info(audit_equinix(read_devices(csv),args.region_equinix),region)),csv,region)

    else:
        parser.print_help()
        return

if __name__ == "__main__":
    port_re()
