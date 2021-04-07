#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
'''
Author: Jason Guo (jasguo@amazon.com) and Edi Wibowo (ewi@amazon.com)
Date: 17 Aug 2020

This script is to find available interfaces on vc-edg routers. 
Available interfaces are free and not oversubscribed.

The calculation rule of subscription:
- FPC "MPC 3D 16x 10GE" can have a maximum of 16 available interfaces 
with each PIC having a maximum of 3 available interfaces
- FPC "MPC4E-3D-32XGE-SFPP" can have a maximum of 16 available interfaces when redundancy is enabled 
with each PPE (PICs 0-1 or PICs 2-3) having a maximum of 13 available interfaces


For example:
INPUT:
Hostnames: iad6-vc-edg-r311,iad6-vc-edg-r312

OUTPUT:
Hostname: iad6-vc-edg-r311
available ports:
xe-0/0/2
xe-0/2/3
xe-1/0/3
xe-1/1/3
number of available ports: 4
---
Hostname: iad6-vc-edg-r312
available ports:
xe-0/0/2
xe-0/2/3
xe-0/3/1
xe-1/1/2
xe-1/1/3
xe-1/2/2
number of available ports: 6

'''

import re
import sys

from isd_tools_dev.modules import nsm as nsm_isd
from dxd_tools_dev.modules import nsm as nsm_dxd

def populate_slot_and_subslot(used_interfaces, fpc_dict, slot_dict, subslot_dict):
    for u in used_interfaces:

        found = re.match("xe-(\d+)/(\d+)/(\d+)", u)
        if found:
            slot_num = found.groups()[0]
            subslot_num = found.groups()[1]

            if slot_num in slot_dict.keys():
                slot_dict[slot_num] += 1
            else:
                slot_dict[slot_num] = 1

            fpc_slot = "FPC {}".format(slot_num)

            if fpc_dict[fpc_slot] == "MPC 3D 16x 10GE":
                slot_subslot_num = "{}-{}".format(slot_num, subslot_num)
            else:
                if subslot_num == '0' or subslot_num == '1':
                    ppe = 'A'
                else:
                    ppe = 'B'
                slot_subslot_num = "{}-{}".format(slot_num, ppe)

            if slot_subslot_num in subslot_dict.keys():
                subslot_dict[slot_subslot_num] += 1
            else:
                subslot_dict[slot_subslot_num] = 1

def is_port_available(slot_num, subslot_num, slot_dict, subslot_dict):
    slot_available = False
    subslot_available = False

    fpc_slot = "FPC {}".format(slot_num)

    if fpc_dict[fpc_slot] == "MPC 3D 16x 10GE":
        if slot_dict.get(slot_num) != None and slot_dict.get(slot_num) < 16:
            slot_available = True
            
        slot_subslot_num = "{}-{}".format(slot_num,subslot_num)
        
        if subslot_dict.get(slot_subslot_num) != None and subslot_dict.get(slot_subslot_num) < 3:
            subslot_available = True
    else:
        if slot_dict.get(slot_num) == None or slot_dict.get(slot_num) < 24:
            slot_available = True

        if subslot_num == '0' or subslot_num == '1':
            ppe = 'A'
        else:
            ppe = 'B'
        
        slot_subslot_num = "{}-{}".format(slot_num,ppe)
        
        if subslot_dict.get(slot_subslot_num) == None or subslot_dict.get(slot_subslot_num) < 13:
            subslot_available = True

    if slot_available and subslot_available:
        if slot_num in slot_dict.keys():
            slot_dict[slot_num] += 1
        else:
            slot_dict[slot_num] = 1
        
        if slot_subslot_num in subslot_dict.keys():
            subslot_dict[slot_subslot_num] += 1
        else:
            subslot_dict[slot_subslot_num] = 1
        
        return True
    
    return False

def get_interface_lists(nsm_isd_raw):
    free_interfaces = list()
    excluded_interfaces = list()
    used_interfaces = list()
    
    for interface in nsm_isd_raw:
        if interface['class'] == 'physical' and 'xe-' in interface['name']:
            if "aggregation" in interface.keys() and interface['capacity_status'] == 'free':
                used_interfaces.append(interface['name'])
            elif interface['status'] == "down" and interface['interface_description'] == '' and interface['capacity_status'] == "free":
                free_interfaces.append(interface['name'])
            else:
                used_interfaces.append(interface['name'])
            
            # Ports that are excluded from subscription calculation
            if 'ae9' in interface['interface_description']:
             excluded_interfaces.append(interface['name'])

    return free_interfaces,used_interfaces,excluded_interfaces

def sort_key(f):
    slot_num = 0
    subslot_num = 0
    port_num = 0
    found = re.match("xe-(\d+)/(\d+)/(\d+)", f)
    if found:
        slot_num = found.groups()[0]
        subslot_num = found.groups()[1]
        port_num = found.groups()[2]

    return int(slot_num), int(subslot_num), int(port_num)

def get_available_interfaces(free_interfaces, slot_dict, subslot_dict):
    available_interfaces = []

    free_interfaces.sort(key=sort_key)

    for f in free_interfaces:
        found = re.match("xe-(\d+)/(\d+)/(\d+)", f)
        if found:
            slot_num = found.groups()[0]
            subslot_num = found.groups()[1]
            if is_port_available(slot_num, subslot_num, slot_dict, subslot_dict):
                available_interfaces.append(f)

    return  available_interfaces

def get_new_interfaces():
    print(fpc_dict)
    new_linecard = input("Slots of new line cards (mutiple linecards can be added with comma delimiter or Press Enter to skip): ")
    
    new_interfaces = []
    fpc = new_linecard.split(',')

    if len(fpc) == 0:
        return new_interfaces

    pic =[x for x in range(4)]
    ports = [x for x in range(8)]
    
    for port in ports:
        for p in pic:
            for f in fpc:
                intf = "xe-{}/{}/{}".format(f,p,port)
                new_interfaces.append(intf)

    '''
    print("new interfaces:")
    for n in new_interfaces:
        print(n)
    '''

    slot_dict = {}
    subslot_dict = {}

    # Allocate ports from the new ports
    allocated_interfaces = []
    number_required_ports = 100
    #number_required_ports = int(input("Number of required ports: "))

    counter = 0
    for n in new_interfaces:
        slot_available = False
        subslot_available = False
  
        found = re.match("xe-(\d+)/(\d+)/(\d+)", n.strip())

        if found:
            
            slot_num = found.groups()[0]
            subslot_num = found.groups()[1]

            if slot_dict.get(slot_num) == None or slot_dict.get(slot_num) < 16:
                slot_available = True

            if subslot_num == '0' or subslot_num == '1':
                ppe = 'A'
            else:
                ppe = 'B'

            slot_subslot_num = "{}-{}".format(slot_num,ppe)
        
            if subslot_dict.get(slot_subslot_num) == None or subslot_dict.get(slot_subslot_num) < 13:
                subslot_available = True

            if slot_available and subslot_available:
                if slot_num in slot_dict.keys():
                    slot_dict[slot_num] += 1
                else:
                    slot_dict[slot_num] = 1
                if slot_subslot_num in subslot_dict.keys():
                    subslot_dict[slot_subslot_num] += 1
                else:
                    subslot_dict[slot_subslot_num] = 1
                counter += 1
                allocated_interfaces.append(n)
                
                '''
                if counter >= number_required_ports:
                    #allocated_interfaces.sort(key=sort_key)
                    return allocated_interfaces
                '''
                
    #allocated_interfaces.sort(key=sort_key)
    return allocated_interfaces
    
if __name__ == '__main__':
    hostnames = input("Hostnames (mutiple hostnames can be entered with comma delimiter): ").split(',')
    
    for hostname in hostnames:
        print("---")
        print("Hostname: {}".format(hostname))
        int_nsm_isd = nsm_isd.get_raw_device(hostname)['interfaces']
        
        free_interfaces, used_interfaces, excluded_interfaces = get_interface_lists(int_nsm_isd)
        
        free_interfaces.sort()
        used_interfaces.sort()
        excluded_interfaces.sort()

        '''
        print("free interfaces:")
        for f in free_interfaces:
            print(f)

        print("used interfaces:")
        for u in used_interfaces:
            print(u)

        print("excluded interfaces:")
        for e in excluded_interfaces:
            print(e)
        '''

        # Remove excluded interfaces before calculating the interface subscription
        used_interfaces_set = set(used_interfaces)
        used_interfaces_set = used_interfaces_set.difference(excluded_interfaces)
        used_interfaces = list(used_interfaces_set)

        hard = nsm_dxd.get_device_hardware_from_nsm(hostname)
        fpc_dict = hard['FPC']
        
        slot_dict = {}
        subslot_dict = {}

        populate_slot_and_subslot(used_interfaces, fpc_dict, slot_dict, subslot_dict)

        # Get available ports which are not oversubscribed based on slot and subslot availability
        available_interfaces = get_available_interfaces(free_interfaces, slot_dict, subslot_dict)

        print("available interfaces:")
        for a in available_interfaces:
            print(a)
        print("number of available interfaces: {}".format(len(available_interfaces)))

        new_interfaces = get_new_interfaces()
        
        new_interfaces.sort(key=sort_key)

        print("new interfaces:")
        for n in new_interfaces:
            print(n)
