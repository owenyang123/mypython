#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import jukebox
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from dxd_tools_dev.modules import maestro_db
from dxd_tools_dev.modules import nsm
from dxd_tools_dev.datastore import ddb


def build_edg_dict(region_list,region):
    edges_dict = {}
    output_list = []
    query = "select d.hostname, eg.* from devices d join interfaces i on i.device_id = d.id and i.intftype = 'physical' join south_interfaces si on si.physical_interface_id = i.id join edg_groups eg on eg.nm_pool_id = si.nm_pool_id where eg.edg_group_type = 'ExternalCustomer';"
    f = maestro_db.query_Maestro(region,query)
    edges_dict['region'] = region
    edges_dict["Devices"] = {}
    devices_list_op = nsm.get_devices_from_nsm('vc-edg',region,"OPERATIONAL")
    devices_list_op.extend(nsm.get_devices_from_nsm('vc-edg',region,"TURNED_UP"))
    devices_list_op.extend(nsm.get_devices_from_nsm('vc-edg',region,"MAINTENANCE"))
    for line in f.splitlines():
        if "|" in line: 
            output_list.append([l.strip() for l in line.split("|")])
    for data_list in output_list[1:]:
        if "." in data_list[1]:
            device = data_list[1].split(".")[0]
            if device in devices_list_op:
                edges_dict["Devices"][device] = {}
                edges_dict["Devices"][device]['Type'] = "Commercial"
                edges_dict["Devices"][device]['name'] = data_list[3]

        elif data_list[1] in  devices_list_op:
            device =  data_list[1]
            edges_dict["Devices"][device] = {}
            edges_dict["Devices"][device]['Type'] = "Commercial"
            edges_dict["Devices"][device]['name'] = data_list[3]
    table = ddb.get_ddb_table('vc-edg-audit-table')
    ddb.put_item_to_table(table,edges_dict)
    region_list.append("INFO: completed "+region)
    return region_list
 


def main():
    region_list = []
    REGIONS = ['iad', 'pdx','bjs', 'fra', 'bom','hkg', 'nrt', 'cmh', 'arn', 'dub','syd', 'lhr', 'yul', 'kix', 'cdg', 'bah', 'zhy', 'sfo','sin', 'icn', 'gru', 'cpt', 'mxp']
    print("INFO:Updating the table for all regions")
    with ThreadPoolExecutor(max_workers=10) as executor:
        f = {executor.submit(build_edg_dict,region_list,region) for region in REGIONS }
        for future in concurrent.futures.as_completed(f):
            result = future.result()
        for item in region_list:
            print(item)

main()
