#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import nsm
from multiprocessing import Pool
import logging

links = True

def get_device_border_bandwidth(device_name):
    total_border_bandwidth = int()
    device_dict = dict()
    try:
        device_interfaces = nsm.get_device_detail_from_nsm(device_name,links)['Interfaces']
        for interface in device_interfaces:
            if interface['Class'] == 'aggregate' and 'br-tra' in interface['Description']:
                total_border_bandwidth += int(interface['Bandwidth_Mbps'])/1000

        device_dict.update({'name':device_name,'bandwidth':total_border_bandwidth})
        return device_dict

    except:
        logging.error("Failed to retrieve data from NSM stack for {}".format(device_name))
        pass

def get_site_border_bandwidth(site, devices_bandwidth):
    total_site_bandwidth = int()
    site_dict = dict()
    for bandwidth in devices_bandwidth:
        if site == bandwidth.get()['name'].split('-')[0]:
            total_site_bandwidth += bandwidth.get()['bandwidth']
    site_dict.update({'site':site.upper(),'site_bandwidth':total_site_bandwidth})
    return site_dict

def get_sites(devices_bandwidth):
    sites = list()
    for site in devices_bandwidth:
        sites.append(site.get()['name'].split('-')[0])
    return list(set(sites))

def main():
    results = list()
    results_filtered = list()
    site_results = list()
    sites = list()
    device_list = nsm.get_devices_from_nsm("name:/.*-vc-(dar|car)-.*/")
    pool = Pool(16)

    for device in device_list:
        if device != 'sfo5-5-vc-car-r1':
            results.append(pool.apply_async(get_device_border_bandwidth, args = (device,)))

    for result in results:
        try:
            if result.get()['name']:
                results_filtered.append(result)
        except:
            pass

    sites = get_sites(results_filtered)

    for site in sites:
        site_results.append(get_site_border_bandwidth(site, results_filtered))

    for site in site_results:
        print('{} has {} Gbps towards Border'.format(site['site'],site['site_bandwidth']))

if __name__ == '__main__':
    main()
