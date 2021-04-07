#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from jinja2 import Environment, BaseLoader
import sys
import argparse
import re
import subprocess
import os
import getpass
import logging
import pandas as pd
from dxd_tools_dev.modules import mcm, jukebox, maestro_db, veracity




logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',level=logging.INFO)
query = str()

def generate_port_dict(device,port_list):
    logging.info("getting ports from Maestro-DB and verifying all ports are deleted")
    maestro_dict = {}
    maestro_dict[device] = {}
    device_info = jukebox.get_device_detail(device)
    device_region = device_info.data.device.realm
    
    query_list = []
    First = True
    for interface in port_list:
        if First:
            query_list.append("ppr.interface_name = '"+interface+"' ")
            First = False
        else:
            query_list.append("or ppr.interface_name = '"+interface+"' ")
    global query 
    query = "select d.hostname, ppr.interface_name, pp.available_at, pc.obfuscated_id, pc.owner_account, pc.state from physical_port_reservations ppr join physical_ports pp on pp.physical_port_reservation_id=ppr.id join physical_connections pc on pc.physical_port_id=pp.id join devices d on d.id=ppr.device_id where d.hostname like '"+device+"%' and ("+"".join(query_list)+") order by pp.available_at asc;"    
    Maestro_Result = maestro_db.query_Maestro(device_region,query)
    for item in Maestro_Result.splitlines():
        if not '+' in item and not 'hostname' in item and not 'row' in item and item.strip() !='':
            interface = item.split("|")[2].strip()
            maestro_dict[device][interface] = {}
            maestro_dict[device][interface]["Status"] = item.split("|")[-2].strip()

    for interface in port_list:
        if interface not in maestro_dict[device].keys():
            maestro_dict[device][interface] = {}
            maestro_dict[device][interface]["Status"] = 'deleted'

        elif maestro_dict[device][interface]["Status"] != 'deleted':
            logging.error("interface {} is not in deleted state".format(interface))
            sys.exit(1)

    return maestro_dict



def check_config_update_dict(maestro_dict):

    logging.info("getting routing-instances for the ports")
    
    device =list( maestro_dict.keys())[0]
    port_list = list( maestro_dict[device].keys())
    
    completed_process = subprocess.run('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {}  latest --file set-config --uncensored'.format(device),shell=True,stdout=subprocess.PIPE)
    config = completed_process.stdout.decode('ascii')

    for interface in port_list:
        maestro_dict[device][interface]["VRF"] = []
        regex = "set routing-instances .* interface "+interface+"\\..*"
        for config_line in re.findall(regex,config):
            maestro_dict[device][interface]["VRF"].append(config_line.split()[2])

        if not maestro_dict[device][interface]["VRF"]:
            logging.error('Interface {} has no routing-instances in the device please check that you have selected the right interfaces'.format(interface))
            sys.exit(1)

    return maestro_dict

def create_var_config_files(maestro_dict,mcm_number,query):

    logging.info("creating var and config files")

    VRF_DELETION = []
    mcm_number = mcm_number.upper()
    os.mkdir(mcm_number)
    os.mkdir('{}/{}'.format(mcm_number,'files'))
    device =list( maestro_dict.keys())[0]
    port_list = list( maestro_dict[device].keys())
    device_info = jukebox.get_device_detail(device)
    device_region = device_info.data.device.realm
    

    for interface in port_list:
        VRF_DELETION.extend(maestro_dict[device][interface]["VRF"])
    VRF_DELETION = list(set(VRF_DELETION))
    if len(VRF_DELETION) >= 300:
        logging.error('VRFs to delete are more than 300 lower the number of ports number and run it again current number is '+len(VRF_DELETION))
        sys.exit(1)
          
    VRF_DELETION_lists = [ VRF_DELETION[vrf:vrf + 10] for vrf in range(0, len(VRF_DELETION), 10)]

    var_tempelate = '''
## set QUERY = "{}"
## set REGION = "{}"
## set MCM = "{}"
## set ROUTER = "{}"
## set Delete_PORTS = {}
## set VRF_DELETION = {}
\n\n\n\nset_working_dir('brazil://DxVpnCM2014/cm/{}/{}/files','<ENTER_COMMIT_ID>')
{{%- include 'brazil://DxVpnCMTemplates/templates/delete_stale_objects.jt' %}}
    '''.format(query, device_region, mcm_number, device, port_list, VRF_DELETION_lists, getpass.getuser(), mcm_number)

    config_tempelate = '''
interfaces {
{% for interface in port_list -%}
{{"           "}}delete: {{interface}};
{% endfor -%}
}

routing-instances {
{% for vrf in VRF_DELETION -%}
{{"           "}}delete: {{vrf}};
{% endfor -%}
}
'''
    template = Environment(loader=BaseLoader).from_string(config_tempelate)
    config = template.render(port_list = port_list,VRF_DELETION = VRF_DELETION )

    with open('{}/{}.var'.format(mcm_number,mcm_number), 'w') as var:
        var.write(var_tempelate)

    with open('{}/{}/{}-remove.push'.format(mcm_number,'files',device), 'w') as config_file:
        config_file.write(config)

    logging.info("All files created in folder {}".format(mcm_number))


def migrate_in_use_ports_assesment(source_device_list, destination_device_list):
    source = {}
    destination = {}
    for source_device in source_device_list:
        device_info = jukebox.get_device_detail(source_device)
        region = device_info.data.device.realm
        source[source_device] = {}
        dxdb_info = maestro_db.get_dx_dashboard_info(source_device)
        query_list = []
        output_list = []
        First = True
        for dxdb_row in dxdb_info:
            if dxdb_row['in_use'] == '1':
                source[source_device][dxdb_row['interface']] = {}
                source[source_device][dxdb_row['interface']]["Account_number"] = []
                if First:
                    query_list.append("ppr.interface_name = '"+dxdb_row['interface']+"' ")
                    First = False
                else:
                    query_list.append("or ppr.interface_name = '"+dxdb_row['interface']+"' ")
        query = "select distinct d.hostname, ppr.interface_name, pc.owner_account, pc.state from physical_connections pc join physical_ports pp on pp.id=pc.physical_port_id join physical_port_reservations ppr on ppr.id=pp.physical_port_reservation_id join devices d on d.id=ppr.device_id where  pc.state = 'available' and d.hostname like '"+source_device+"%' and ("+"".join(query_list)+") ;\n"
        f =  maestro_db.query_Maestro(region,query)

        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")]) 

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                source[data_list[1].split(".")[0]][data_list[2]]["Account_number"].append(data_list[3])

            else:
                source[data_list[1].split(".")[0]][data_list[2]]["Account_number"].append(data_list[3])


    for destination_device in destination_device_list:
        destination[destination_device] = {}
        destination[destination_device]["Account_number"] = []
        destination[destination_device]["Added_Account_number"] = []
        query2 = "select distinct d.hostname, ppr.interface_name, pc.owner_account, pc.state from physical_connections pc join physical_ports pp on pp.id=pc.physical_port_id join physical_port_reservations ppr on ppr.id=pp.physical_port_reservation_id join devices d on d.id=ppr.device_id where  pc.state = 'available' and d.hostname like '"+destination_device+"%' ;\n"
        f =  maestro_db.query_Maestro(region,query2)
        output_list = []
        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")]) 

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                destination[data_list[1].split(".")[0]]["Account_number"].append(data_list[3])

            else:
                destination[data_list[1].split(".")[0]]["Account_number"].append(data_list[3])


    for source_device in source.keys():
        for interface in source[source_device].keys():
            assesment_finished = False
            for destination_device  in destination.keys():
                if not assesment_finished:
                    j = len(source[source_device][interface]["Account_number"])
                    for i in range(0, j):
                        if source[source_device][interface]["Account_number"][i] not in destination[destination_device]["Account_number"] and i == (j-1):
                            source[source_device][interface]['migration_assessment'] = 'ok to migrate to '+destination_device
                            destination[destination_device]["Added_Account_number"] += source[source_device][interface]["Account_number"]
                            assesment_finished = True       
                            print("device {} and interface {} is {}".format(source_device,interface,source[source_device][interface]['migration_assessment']))       
                        elif source[source_device][interface]["Account_number"][i] not in destination[destination_device]["Account_number"]:
                            continue    
                        elif source[source_device][interface]["Account_number"][i] in destination[destination_device]["Account_number"]:
                            source[source_device][interface]['migration_assessment'] = 'Not ok to migrate to '+destination_device
                            print("device {} and interface {} is {}".format(source_device,interface,source[source_device][interface]['migration_assessment']))                            
                            break
                else:
                    break
        for destination_device in destination.keys():
            destination[destination_device]["Account_number"] += destination[destination_device]["Added_Account_number"]
    return source, destination






def create_migration_mcm_1(cutsheet,cutsheet_mcm_number,step1,step2):
    print('INFO: Creating migration mcm make sure these columns exist in your sheet as:\n  A_device A_interfaceName speed A_cage A_rack A_patchPanel A_port Z_device Z_interfaceName speed Z_cage Z_rack Z_patchPanel Z_port\n')
    dint_dict = {}
    xls = pd.ExcelFile(cutsheet)
    df = pd.read_excel(xls, 'Sheet1')
    df = df.sort_values('A_device')
    df = df.dropna(how='all').reset_index(drop=True)
    df = df.astype('str')
    excel_dict = df.to_dict()


    Q_list = []
    mcm_devices = []

    for item1 in excel_dict['A_device'].items():
        if '.' in item1[1]:
            device = item1[1].split('.')[0]
        else:
            device = item1[1]
        dint_dict[device] = {}
        dint_dict[device]["INTERFACES"] = {}



    for i in range(0, len(df)):
        if '.' in excel_dict['A_device'][i]:
            device = excel_dict['A_device'][i].split('.')[0]
        else:
            device = excel_dict['A_device'][i]

        mcm_devices.append(device)
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]] = {}
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]]["Destination_Device"] = excel_dict['Z_device'][i]
        mcm_devices.append(excel_dict['Z_device'][i])
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]]["Destination_interface"] = excel_dict['Z_interfaceName'][i]
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]]["DXcons"] = {}


    for device in dint_dict.keys():
        device_info = jukebox.get_device_detail(device)
        region = device_info.data.device.realm
        
        site = device.split('-')[0]


        Q_list = []
        First = True
        for interface in dint_dict[device]["INTERFACES"].keys():
            if First:
                Q_list.append("ppr.interface_name = '"+interface+"' ")
                First = False
            else:
                Q_list.append("or ppr.interface_name = '"+interface+"' ")
        QUERY = "select d.hostname, ppr.interface_name, pc.lag_connection_id, pc.parent_connection_id, pc.bandwidth_mbps, pc.allow_dependent_connections, l.code, pp.available_at, pc.obfuscated_id, pc.name,  pc.owner_account, pc.state from physical_port_reservations ppr join physical_ports pp on pp.physical_port_reservation_id=ppr.id join physical_connections pc on pc.physical_port_id=pp.id join devices d on d.id=ppr.device_id join direct_connect_locations l on l.id=ppr.direct_connect_location_id where d.hostname like '"+device+"%' and ("+"".join(Q_list)+") and pc.state = 'available' order by pc.allow_dependent_connections desc;"


        f =  maestro_db.query_Maestro(region,QUERY)
        output_list = []
        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")]) 

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                device_name = data_list[1].split(".")[0]
            else:
                device_name = data_list[1]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]] = {}
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Owner_account"] = data_list[11]
            if data_list[5] == '10000':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["bandwidth"] = '10gbps'
            elif data_list[5] == '1000':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["bandwidth"] = '1gbps'
            elif data_list[5] == '100000':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["bandwidth"] = '100gbps'

            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Name"] = data_list[10]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Location"] = data_list[7]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]['VIFS'] = list()
            if data_list[3] != 'NULL':
                print('interface has a lag coming soon Good Bye!')
                exit()

            if data_list[4] == 'NULL' and data_list[6] == '1':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Partner'
            elif data_list[4] != 'NULL':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Hosted'
            else:
               dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Direct'

    step1_mcm_number = False
    mcm_steps = []
    mcm_devices = list(set(mcm_devices))
    mcm_devices = "\n".join(mcm_devices)
    mcm_info = mcm.mcm_creation("mcm_title_overview_customer_migration", mcm_devices, site, cutsheet_mcm_number,step1,step2,step1_mcm_number)
    mcm_id = mcm_info[0]
    mcm_uid = mcm_info[1]
    mcm_overview = mcm_info[2]

    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport={'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)

    print('INFO: https://mcm.amazon.com/cms/{} created'.format(mcm_id))

    

    for device in dint_dict.keys():
        for interface in dint_dict[device]["INTERFACES"].keys():

            for dxcon in dint_dict[device]["INTERFACES"][interface]["DXcons"].keys():
                if dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Type"] == 'Direct':
                    veracity_dict = veracity.issue_veracity_command(region,f'/apollo/env/VeracityServiceCLI/bin/veracity-cli find-customer-limits --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --property-name OvertureService.feature.control.allow.logicalRedundancy' )
                    if veracity_dict['customerLimits'][0]['propertyValue'] == 'allowed':
                        dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['logicalRedundancy'] = f'''

-verify logical redundacy  allowed:

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-customer-limits --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --property-name OvertureService.feature.control.allow.logicalRedundancy
```

'''

                    else:
                        dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['logicalRedundancy'] = f'''

-verify its not allowed and then make the account logical redundacy default

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-customer-limits --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --property-name OvertureService.feature.control.allow.logicalRedundancy
```

```
apollo/env/VeracityServiceCLI/bin/veracity-cli remove-customer-limit --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]}  --property-name OvertureService.feature.control.allow.logicalRedundancy
```

'''                        



                    mcm_steps.append({'title':f'Create and approve new dxcons for existing dxcon {dxcon}','time':20,'description':f'''

ssh2hc awsdx-veracity-{region}

- Get status of all the vifs/BGP neighbors on interface with command and device itself.


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {dxcon}
```


```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon} 
```


{dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['logicalRedundancy']}



- Create new dxcon

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli create-connection --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --location {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Location"]} --connection-name {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Name"]}-{mcm_id} --bandwidth {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["bandwidth"]}
```

- Make the destination port available in dx-dashboard:

```
using tt with hostname in title/description 

make {dint_dict[device]["INTERFACES"][interface]["Destination_Device"]}  {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} avaible in DXDB

https://directconnectdashboard.corp.amazon.com/#/port_reservations?device={dint_dict[device]["INTERFACES"][interface]["Destination_Device"]}

```


- Approve new dxcon:

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli approve-connection --owner-account  {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --obfuscated-id $GET-IT-FROM-COMMAND-ABOVE --device-host-name {dint_dict[device]["INTERFACES"][interface]["Destination_Device"]} --interface-name {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]}  --identity {getpass.getuser()}
```
- New dxcon should be in available state .


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id $GET-IT-FROM-COMMAND-ABOVE
```

''','rollback':f'''

Delete the newly creted DXCON 

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli delete-physical-connection --caller-id {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --obfuscated-id $GET-IT-FROM-COMMAND-ABOVE
```
'''})





                elif dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Type"] == 'Partner':
                    Partner_DXCON = dxcon
                    veracity_dict = veracity.issue_veracity_command(region,f'/apollo/env/VeracityServiceCLI/bin/veracity-cli find-customer-limits --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --property-name OvertureService.feature.control.allow.logicalRedundancy' )
                    if veracity_dict['customerLimits'][0]['propertyValue'] == 'allowed':
                        dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['logicalRedundancy'] = f'''

-verify logical redundacy  allowed:

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-customer-limits --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --property-name OvertureService.feature.control.allow.logicalRedundancy
```

'''

                    else:
                        dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['logicalRedundancy'] = f'''

-verify its not allowed and then make the account logical redundacy default

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-customer-limits --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --property-name OvertureService.feature.control.allow.logicalRedundancy
```

```
apollo/env/VeracityServiceCLI/bin/veracity-cli remove-customer-limit --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]}  --property-name OvertureService.feature.control.allow.logicalRedundancy
```

''' 

                    mcm_steps.append({'title':f'Create and approve new dxcons for existing Partner dxcon {dxcon}','time':20,'description':f'''

ssh2hc awsdx-veracity-{region}



- Get status of all the vifs/BGP neighbors on interface with command and device itself.


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {dxcon}
```


```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon} 
```


{dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['logicalRedundancy']}


- Create new dxcon

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli create-connection --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --location {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Location"]} --connection-name {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Name"]}-{mcm_id} --bandwidth {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["bandwidth"]}
```


- Make the destination port available in dx-dashboard:


```
using tt with hostname in title/description 

make {dint_dict[device]["INTERFACES"][interface]["Destination_Device"]}  {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} avaible in DXDB

https://directconnectdashboard.corp.amazon.com/#/port_reservations?device={dint_dict[device]["INTERFACES"][interface]["Destination_Device"]}

```



- Approve new dxcon:


```
/apollo/env/VeracityServiceCLI/bin/veracity-cli approve-connection --owner-account  {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --obfuscated-id $GET-IT-FROM-COMMAND-ABOVE --device-host-name {dint_dict[device]["INTERFACES"][interface]["Destination_Device"]} --interface-name {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} --identity {getpass.getuser()}

```



- make the new partner connection accept hosted connections

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli allow-dependent-connections --connection-id $GET-IT-FROM-COMMAND-ABOVE --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --allow-dependent
```






- New dxcon should be in available state.


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id $GET-IT-FROM-COMMAND-ABOVE
```






''','rollback':f'''

Delete the newly creted DXCON 

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli delete-physical-connection --caller-id {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --obfuscated-id $GET-IT-FROM-COMMAND-ABOVE
```
'''})
                
                else:
                    continue


    mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)

    print('INFO: {} successfully updated, review and submit for approvals\n'.format(mcm_id))


























def create_migration_mcm_2(cutsheet,cutsheet_mcm_number,step1,step2,step1_mcm_number):
    print('INFO: Creating migration mcm make sure these columns exist in your sheet as:\n  A_device A_interfaceName speed A_cage A_rack A_patchPanel A_port Z_device Z_interfaceName speed Z_cage Z_rack Z_patchPanel Z_port\n')
    dint_dict = {}
    destination_dint_dict = {}
    xls = pd.ExcelFile(cutsheet)
    df = pd.read_excel(xls, 'Sheet1')
    df = df.sort_values('A_device')
    df = df.dropna(how='all').reset_index(drop=True)
    df = df.astype('str')
    excel_dict = df.to_dict()


    Q_list = []
    mcm_devices = []

    for item1 in excel_dict['A_device'].items():
        if '.' in item1[1]:
            device = item1[1].split('.')[0]
        else:
            device = item1[1]
        dint_dict[device] = {}
        dint_dict[device]["INTERFACES"] = {}

    for item1 in excel_dict['Z_device'].items():
        if '.' in item1[1]:
            Z_device = item1[1].split('.')[0]
        else:
            Z_device = item1[1]
        destination_dint_dict[Z_device] = {}
        destination_dint_dict[Z_device]["INTERFACES"] = {}



    for i in range(0, len(df)):
        if '.' in excel_dict['A_device'][i]:
            device = excel_dict['A_device'][i].split('.')[0]
        else:
            device = excel_dict['A_device'][i]

        if '.' in excel_dict['Z_device'][i]:
            Z_device = excel_dict['Z_device'][i].split('.')[0]
        else:
            Z_device = excel_dict['Z_device'][i]

        mcm_devices.append(device)
        mcm_devices.append(Z_device)

        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]] = {}
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]]["Destination_Device"] = Z_device    
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]]["Destination_interface"] = excel_dict['Z_interfaceName'][i]
        dint_dict[device]["INTERFACES"][excel_dict['A_interfaceName'][i]]["DXcons"] = {}

        destination_dint_dict[Z_device]["INTERFACES"][excel_dict['Z_interfaceName'][i]] = {}
        destination_dint_dict[Z_device]["INTERFACES"][excel_dict['Z_interfaceName'][i]]["DXcons"] = {}

    for device in destination_dint_dict.keys():
        device_info = jukebox.get_device_detail(device)
        region = device_info.data.device.realm

        Q_list = []
        First = True
        for interface in destination_dint_dict[device]["INTERFACES"].keys():
            if First:
                Q_list.append("ppr.interface_name = '"+interface+"' ")
                First = False
            else:
                Q_list.append("or ppr.interface_name = '"+interface+"' ")
        QUERY = "select d.hostname, ppr.interface_name, pc.lag_connection_id, pc.parent_connection_id, pc.bandwidth_mbps, pc.allow_dependent_connections, l.code, pp.available_at, pc.obfuscated_id, pc.name,  pc.owner_account, pc.state from physical_port_reservations ppr join physical_ports pp on pp.physical_port_reservation_id=ppr.id join physical_connections pc on pc.physical_port_id=pp.id join devices d on d.id=ppr.device_id join direct_connect_locations l on l.id=ppr.direct_connect_location_id where d.hostname like '"+device+"%' and ("+"".join(Q_list)+") and pc.state = 'available' order by pc.allow_dependent_connections desc;"


        f =  maestro_db.query_Maestro(region,QUERY)
        output_list = []
        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")]) 

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                device_name = data_list[1].split(".")[0]
            else:
                device_name = data_list[1]
            destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]] = {}
            destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Owner_account"] = data_list[11]
            destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["bandwidth"] = data_list[5]
            destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Name"] = data_list[10]
            destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Location"] = data_list[7]
            destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]['VIFS'] = list()
            if data_list[3] != 'NULL':
                print('interface has a lag coming soon Good Bye!')
                exit()

            if data_list[4] == 'NULL' and data_list[6] == '1':
                destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Partner'
            elif data_list[4] != 'NULL':
                destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Hosted'
            else:
               destination_dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Direct'

    for device in dint_dict.keys():
        device_info = jukebox.get_device_detail(device)
        region = device_info.data.device.realm
        
        site = device.split('-')[0]


        Q_list = []
        First = True
        for interface in dint_dict[device]["INTERFACES"].keys():
            if First:
                Q_list.append("ppr.interface_name = '"+interface+"' ")
                First = False
            else:
                Q_list.append("or ppr.interface_name = '"+interface+"' ")
        QUERY = "select d.hostname, ppr.interface_name, pc.lag_connection_id, pc.parent_connection_id, pc.bandwidth_mbps, pc.allow_dependent_connections, l.code, pp.available_at, pc.obfuscated_id, pc.name,  pc.owner_account, pc.state from physical_port_reservations ppr join physical_ports pp on pp.physical_port_reservation_id=ppr.id join physical_connections pc on pc.physical_port_id=pp.id join devices d on d.id=ppr.device_id join direct_connect_locations l on l.id=ppr.direct_connect_location_id where d.hostname like '"+device+"%' and ("+"".join(Q_list)+") and pc.state = 'available' order by pc.allow_dependent_connections desc;"


        f =  maestro_db.query_Maestro(region,QUERY)
        output_list = []
        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")]) 

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                device_name = data_list[1].split(".")[0]
            else:
                device_name = data_list[1]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]] = {}
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Owner_account"] = data_list[11]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["bandwidth"] = data_list[5]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Name"] = data_list[10]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Location"] = data_list[7]
            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]['VIFS'] = list()
            if data_list[3] != 'NULL':
                print('interface has a lag coming soon Good Bye!')
                exit()

            if data_list[4] == 'NULL' and data_list[6] == '1':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Partner'
            elif data_list[4] != 'NULL':
                dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Hosted'
            else:
               dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[9]]["Type"] = 'Direct'

        QUERY2 = "select d.hostname, ppr.interface_name, pc.obfuscated_id, pc.owner_account as dxcon_owner, pc.parent_connection_id, dc.obfuscated_id, dc.state as dxvif_state, dc.owner_account as dxvif_owner, dc.created_on, dc.available_at from direct_connections dc left join physical_connections pc on dc.physical_connection_id = pc.id left join physical_ports pp on pc.physical_port_id = pp.id left join physical_port_reservations ppr on pp.physical_port_reservation_id = ppr.id left join devices d on ppr.device_id = d.id where d.hostname  like '"+device+"%' and dc.state = 'available'  and ("+"".join(Q_list)+") order by d.hostname, pc.obfuscated_id;"


        f =  maestro_db.query_Maestro(region,QUERY2)
        output_list = []
        for line in f.splitlines():
            if "|" in line: 
                output_list.append([l.strip() for l in line.split("|")]) 

        for data_list in output_list[1:]:
            if "." in data_list[1]:
                device_name = data_list[1].split(".")[0]
            else:
                device_name = data_list[1]

            dint_dict[device_name]['INTERFACES'][data_list[2]]["DXcons"][data_list[3]]['VIFS'].append(data_list[6])

    mcm_steps = []
    mcm_devices = list(set(mcm_devices))
    mcm_devices = "\n".join(mcm_devices)
    mcm_info = mcm.mcm_creation("mcm_title_overview_customer_migration", mcm_devices, site, cutsheet_mcm_number,step1,step2,step1_mcm_number)
    mcm_id = mcm_info[0]
    mcm_uid = mcm_info[1]
    mcm_overview = mcm_info[2]

    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport = {'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ','time':2,'description':'Check and keep monitoring #netsupport slack channel for any Sev2s in the region/AZ'}
    mcm_steps.append(step_ixops)
    mcm_steps.append(step_netsupport)

    print('INFO: https://mcm.amazon.com/cms/{} created'.format(mcm_id))


    for device in dint_dict.keys():
        for interface in dint_dict[device]["INTERFACES"].keys():
            mcm_steps.append({'title': 'Capture interface status light and erros', 'time':10, 'description':f'''ssh {device}\n show interface {interface}\n show interfaces diagnostics optics {interface} | match power | except alarm | except warning \n -repeat 3 times to show no errors \n show interface {interface} | match error'''})

            for dxcon in dint_dict[device]["INTERFACES"][interface]["DXcons"].keys():
                if dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Type"] == 'Direct':
                    for dest_dxcon in destination_dint_dict[dint_dict[device]["INTERFACES"][interface]["Destination_Device"]]["INTERFACES"][dint_dict[device]["INTERFACES"][interface]["Destination_interface"]]["DXcons"].keys():
                        if destination_dint_dict[dint_dict[device]["INTERFACES"][interface]["Destination_Device"]]["INTERFACES"][dint_dict[device]["INTERFACES"][interface]["Destination_interface"]]["DXcons"][dest_dxcon]["Type"] == 'Direct' and step1_mcm_number in destination_dint_dict[dint_dict[device]["INTERFACES"][interface]["Destination_Device"]]["INTERFACES"][dint_dict[device]["INTERFACES"][interface]["Destination_interface"]]["DXcons"][dest_dxcon]["Name"]:
                            destination_dxcon = dest_dxcon
                    mcm_steps.append({'title':f' verify old and new dxcon and re-name destination dxcon {destination_dxcon}  ','time':20,'description':f'''

ssh2hc awsdx-veracity-{region}



- Get status of all the vifs/BGP neighbors on interface on old and new dxcon.


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {dxcon}
```


```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon} 
```

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --physical-connection-obfuscated-id {destination_dxcon}
```



- Rename new dxcon:

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli rename-connection --owner-account  {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --obfuscated-id {destination_dxcon} --connection-name {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Name"]}
```



- Use Krueger to shut the interface:

```
krueger shut {device} {interface} <TT number>
```

- **Ask DCO to move the physical cable from port `{device} {interface}`  to `{dint_dict[device]["INTERFACES"][interface]["Destination_Device"]} {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]}`**

- capture interface status

ssh {dint_dict[device]["INTERFACES"][interface]["Destination_Device"]} \n show interface {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]}\n show interfaces diagnostics optics {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} | match power | except alarm | except warning \n -repeat 3 times to show no errors \n show interface {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} | match error

''','rollback':f'''
- If interface does not get UP physically after the cable movement or it has errors, move cable back to old interface and unshut it using:

```
krueger unshut {device} {interface} <TT number>
```


- Ensure that vifs/BGP on the old interface gets UP after the rollback.

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon} 
```

'''})


                    if dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['VIFS']:

                        description = "- Move the vif:"

                        rollback = f'''If migrated vif is not getting into available state or BGP state is not the same as it was before migration, take DCO help to shift cable back to {interface} and unshut the old interface.

```
krueger unshut {device} {interface} <TT number>
```

Once that is done transfer first vif back to old dxcon with command:
'''

                        for vif in dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]['VIFS']:
                            description += f'''\n\n ```
apollo/env/VeracityServiceCLI/bin/veracity-cli associate-virtual-interface --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --connection-id {destination_dxcon} --virtual-interface-id {vif}
```'''
                            rollback += f'''\n\n ```
apollo/env/VeracityServiceCLI/bin/veracity-cli associate-virtual-interface --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --connection-id {dxcon} --virtual-interface-id {vif}
```'''
                        description += f'''\n\n- Ensure that vif gets back to available state using:

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {destination_dxcon} 
```

- Confirm that the device is showing up with all the relevant customer objects [MA-PPE,vifs,IPs] and compare BGP status on the vifs with pre-flight data both on device and veracity CLI.

- Reconfirm that all the vifs have been migrated from dxcon:

```
 /apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon}
```

- Delete the old physical connection using: 

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli delete-physical-connection --caller-id {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} {dxcon}
```





- Ensure that old dxcon is removed


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {dxcon}
```



'''

                        rollback += f'''\n\n\n Ensure that vifs/BGPs return back to original state. There is no need to delete the newly generated dxcons.

/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon}

                        '''

                        mcm_steps.append({'title':f'Move the vifs from {dxcon}" to newly generated dxcon ','time':20,'description':description, 'rollback':rollback})




                    else:
                        description = f'''- Delete the old physical connection using: 

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli delete-physical-connection --caller-id {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} {dxcon}
```





- Ensure that old dxcon is removed


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {dxcon}
```
'''

                        mcm_steps.append({'title':f'Delete the old physical connection {dxcon}','time':20,'description':description})




                elif dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Type"] == 'Partner':
                    Partner_DXCON = dxcon 
                    for dest_dxcon in destination_dint_dict[dint_dict[device]["INTERFACES"][interface]["Destination_Device"]]["INTERFACES"][dint_dict[device]["INTERFACES"][interface]["Destination_interface"]]["DXcons"].keys():
                        if destination_dint_dict[dint_dict[device]["INTERFACES"][interface]["Destination_Device"]]["INTERFACES"][dint_dict[device]["INTERFACES"][interface]["Destination_interface"]]["DXcons"][dest_dxcon]["Type"] == 'Partner' and step1_mcm_number in destination_dint_dict[dint_dict[device]["INTERFACES"][interface]["Destination_Device"]]["INTERFACES"][dint_dict[device]["INTERFACES"][interface]["Destination_interface"]]["DXcons"][dest_dxcon]["Name"]:
                            destination_dxcon = dest_dxcon
                    mcm_steps.append({'title':f'verify old and new dxcon and re-name destination dxcon {destination_dxcon} ','time':20,'description':f'''

ssh2hc awsdx-veracity-{region}


- Get status of all the vifs/BGP neighbors on interface on old and new dxcon.


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {dxcon}
```


```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon} 
```

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --physical-connection-obfuscated-id {destination_dxcon}
```


- Rename new dxcon:

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli rename-connection --owner-account  {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Owner_account"]} --obfuscated-id {destination_dxcon} --connection-name {dint_dict[device]["INTERFACES"][interface]["DXcons"][dxcon]["Name"]}
```


- New dxcon should be in available state before proceeding any further with this interface migration.


```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {destination_dxcon}
```


- Use Krueger to shut the interface:

```
krueger shut {device} {interface} <TT number>
```

- **Ask DCO to move the physical cable from port `{device} {interface}`  to `{dint_dict[device]["INTERFACES"][interface]["Destination_Device"]} {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]}`**



- capture interface status

ssh {dint_dict[device]["INTERFACES"][interface]["Destination_Device"]} \n show interface {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]}\n show interfaces diagnostics optics {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} | match power | except alarm | except warning \n -repeat 3 times to show no errors \n show interface {dint_dict[device]["INTERFACES"][interface]["Destination_interface"]} | match error



''','rollback':f'''
- If interface does not get UP physically after the cable movement or it has errors, move cable back to old interface and unshut it using:

```
krueger unshut {device} {interface} <TT number>
```


- Ensure that vifs/BGP on the old interface gets UP after the rollback.

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {dxcon} 
```

'''})
                    description = "- Move the Hosted connections:"
                    rollback = f'''If migrated hosted connections is not getting into available state or BGP state is not the same as it was before migration, take DCO help to shift cable back to {interface} and unshut the old interface.

```
krueger unshut {device} {interface} <TT number>
```
'''

                    for sub_dxcon in dint_dict[device]["INTERFACES"][interface]["DXcons"].keys():
                        if dint_dict[device]["INTERFACES"][interface]["DXcons"][sub_dxcon]["Type"] == 'Hosted':
                            description += f'''\n\n ```
apollo/env/VeracityServiceCLI/bin/veracity-cli associate-hosted-connection --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][sub_dxcon]["Owner_account"]} --connection-id {sub_dxcon} --parent_connection_id {destination_dxcon}
```

- confirm that the hosted connection is availble after the migration:

```
apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {sub_dxcon}

```

- confirm that all the vifs have been migrated to the partner dxcon:

```
 /apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {sub_dxcon}
```


'''

                            rollback += f'''\n\n ```
apollo/env/VeracityServiceCLI/bin/veracity-cli associate-hosted-connection --owner-account {dint_dict[device]["INTERFACES"][interface]["DXcons"][sub_dxcon]["Owner_account"]} --connection-id {sub_dxcon} --parent_connection_id {Partner_DXCON}
```

- confirm that the hosted connection is availble after the migration:

apollo/env/VeracityServiceCLI/bin/veracity-cli get-connections --obfuscated-id {sub_dxcon}

- confirm that all the vifs have been migrated to the partner dxcon:

```
 /apollo/env/VeracityServiceCLI/bin/veracity-cli find-virtual-interfaces --physical-connection-obfuscated-id {sub_dxcon}
```


'''
                    
                    description += f'''\n\n- Ensure that vif gets back to available state using:


- Delete the old physical Partner connection using: 

```
/apollo/env/VeracityServiceCLI/bin/veracity-cli delete-physical-connection --caller-id {dint_dict[device]["INTERFACES"][interface]["DXcons"][Partner_DXCON]["Owner_account"]} {Partner_DXCON}
```

- Ensure that old Partner dxcon is removed

'''


                    rollback += f'''\n\n\n Ensure that vifs/BGPs return back to original state. There is no need to delete the newly generated dxcons.'''

                    mcm_steps.append({'title':f'Move the Hosted connections from {Partner_DXCON}" to newly generated dxcon ','time':20,'description':description, 'rollback':rollback})

                else:
                    continue


    mcm.mcm_update(mcm_id,mcm_uid,mcm_overview,mcm_steps)

    print('INFO: {} successfully updated, review and submit for approvals\n'.format(mcm_id))



def cust_migration_helper():

    main_parser = argparse.ArgumentParser(prog='cust_migration_helper.py', description='Generates Cutsheets, creates mcm for deleting stale objects, creates mcm for migrating customers')
    subparsers = main_parser.add_subparsers(help='commands', dest='command')
    deleting_stale_parser = subparsers.add_parser('delete_stale_Objects', help='Deleting stale objects mcm')
    deleting_stale_parser.add_argument("-d", "--device", required=True, help="specify hostname of device to be delete customer stale Objects on")
    deleting_stale_parser.add_argument("-p", "--ports", help="specify the comma seperated ports to be deleted", required=True)
    deleting_stale_parser.add_argument("-m", "--mcm", help="specify the mcm number", required=True)

    #Cutsheet_parser = subparsers.add_parser('Cutsheet', help='Generates cutsheet mcm for customer migrations')
    #Cutsheet_parser.add_argument("-sd", "--soruce_device", required=True, help="specify hostname of the source router")
    #Cutsheet_parser.add_argument("-dd", "--destination_devices", required=True, help="comma seperated specify hostnames of the destination devices")


    mcm_parser = subparsers.add_parser('migration_mcm', help='Generates step1 and step2 mcms for customer migrations')
    mcm_parser.add_argument("-cf", "--cutsheet_file", required=True, help="specify the path to the cutsheet file")
    mcm_parser.add_argument("-cm", "--cutsheet_mcm_number", required=True, help="specify the cutsheet mcm number ex: MCM-121323232")
    mcm_parser.add_argument("-smn", "--step1_mcm_number", required=False, help="specify the step1 mcm number ex: MCM-121323232")
    mcm_parser.add_argument("--step1", default=False, action="store_true", help="Create mcm for step1 of migration")
    mcm_parser.add_argument("--step2", default=False, action="store_true", help="Create mcm for step2 of migration should be after mcm step1 has completed")




    args = main_parser.parse_args()
    global query 
    if args.command == 'delete_stale_Objects':
        if args.ports.split(","):
            port_list = args.ports.split(",")
            create_var_config_files(check_config_update_dict(generate_port_dict(args.device,port_list)),args.mcm,query)
        else:
            port_list = []
            port_list.append(args.ports)
            create_var_config_files(check_config_update_dict(generate_port_dict(args.device,port_list)),args.mcm)

    elif args.command == 'migration_mcm':
        if args.step1:
            create_migration_mcm_1(args.cutsheet_file,args.cutsheet_mcm_number,args.step1,args.step2)

        elif args.step2:
            create_migration_mcm_2(args.cutsheet_file,args.cutsheet_mcm_number,args.step1,args.step2,args.step1_mcm_number)

    else:
        main_parser.print_help()
        return
   
if __name__ == "__main__":
    cust_migration_helper()
