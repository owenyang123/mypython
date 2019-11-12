#!/usr/bin/env python

from ipaddress import ip_network
from jinja2 import FileSystemLoader
from jinja2 import Environment
from math import ceil

# Global Variables
number_of_ipsec_peers = 1024
ike_policy = 'IKE-POL-MAIN-PSK'
ipsec_policy = 'IPSEC-POL-G2-AES128-SHA1'
instance_type = 'vrf'
as_num = ''
bgp_peer_as_num = '65000'
ipv4_vrf_peer_network_base = ip_network(u'10.86.0.0/21')
ip4v_vrf_inside_network_base = ip_network(u'169.255.0.0/21')
service_set_tmp = 'SERVICE-SET-peering-id-'
instance_rule_name_tmp = 'RULE-peering-id-'
instance_name_tmp = 'MA-PPE-'
mx_output_file = 'mx_router_ipsec_peer_create.cfg'
template_file = 'amzn_ipsec_vrf_configuration.j2'


def create_unique_name(name_template, unique_id):
    return name_template + str(unique_id)


def service_interface_generator(interface_count):
    max_ipsec_peers_per_service_pic = 1024
    max_ints_per_pic = max_ipsec_peers_per_service_pic * 2
    chunk = max_ints_per_pic
    service_interface_slot_list = [5]
    service_interface_pics = 2
    number_of_msdpc_installed = 1
    service_int_name = 'sp'

    # make sure variables above have list of MS-DPC slots equal to the number_of_msdpc_installed. IF there are
    # 2 MS-DPC slots installed then service_interface_slot_list should have 2 slots in the list
    assert len(service_interface_slot_list) == number_of_msdpc_installed
    # todo figure out how to do this
    # make sure the slots are unique, it is not valid to have two MS-DPCs claim the same slot number

    # make sure the number of interface required is within limits of ipsec peers per pic * number of pics *
    # the number of MS-DPCs installed
    assert interface_count * 2 <= ((max_ints_per_pic * service_interface_pics) *
                                   number_of_msdpc_installed)

    if interface_count <= number_of_msdpc_installed * (service_interface_pics * max_ipsec_peers_per_service_pic):

        # determine if the range is < 1024 interfaces (512 IPSec tunnels) if it is we only need to iterate
        # to upper limit
        if interface_count * 2 <= chunk:
            # we don't need to span multiple slots and pics since we are within per pic limits, so just iterate
            # until we have created inside and outside interfaces for number of ipsec peers (2 per peer)
            for peer in range(1, interface_count * 2 + 1):
                slot = service_interface_slot_list[0]
                pic = 1
                yield service_int_name + '-' + str(slot) + '/' + str(pic) + '/0' + '.' + str(peer + 1024)
        else:
            # calculate how many chunks will need to executed (includes partial chunks) so that correct
            # distribution happens over service pics and slots in sequential order: ex. sp-5/0/0 (1024 ints)
            # sp-5/1/0 (1024 ints) etc
            for each_chunk in range(1, int(ceil((interface_count * 2.0) / chunk)) + 1):
                # calculate the number of full chunks
                full_chunks = (interface_count * 2) / chunk
                start_slot = 0
                start_pic = 1
                slot = service_interface_slot_list[start_slot]
                pic = start_pic
                for full_chunk_number in range(1, full_chunks + 1):
                    # create 1024 interfaces
                    for peer in range(1, chunk + 1):
                        yield service_int_name + '-' + str(slot) + '/' + str(pic) + '/0' + '.' + str(peer)
                    # if we completed odd chunk, we only increment the pic and continue with the next 1024 ints
                    if full_chunk_number % 2:
                        pic += 1
                    else:
                        # if we completed even chunk, we increment the slot to next in the list of MS-DPC slots
                        # installed and reset the PIC to zero
                        slot = service_interface_slot_list[start_slot]
                        pic = 0
                # now generate the partial chunk interfaces, remainder
                if (interface_count * 2) % chunk:
                    for peer in range(1, (interface_count * 2) % max_ints_per_pic + 1):
                        yield service_int_name + '-' + str(slot) + '/' + str(pic) + '/0' + '.' + str(peer)

    else:
        raise ValueError('Number of IPSec tunnels exceeds max limit per service pic: MS-DPC installed %d, PIC: %s' 
                         ', Max IPSec Tunnels per PIC: %d' % (number_of_msdpc_installed, service_interface_pics,
                                                              max_ipsec_peers_per_service_pic))


service_set_name_list = []
for number in range(1, number_of_ipsec_peers + 1):
    service_set_name = create_unique_name(service_set_tmp, number + 1024)
    service_set_name_list.append(service_set_name)

instance_rule_name_list = []
for number in range(1, number_of_ipsec_peers + 1):
    instance_rule_name = create_unique_name(instance_rule_name_tmp, number + 1024)
    instance_rule_name_list.append(instance_rule_name)

instance_name_list = []
for number in range(1, number_of_ipsec_peers + 1):
    instance_name = create_unique_name(instance_name_tmp, number)
    instance_name_list.append(instance_name)

route_distinquisher_list = []
for number in range(1, number_of_ipsec_peers + 1):
    route_distinquisher = as_num + ':' + str(number + 2400)
    route_distinquisher_list.append(route_distinquisher)

route_target_list = []
for number in range(1, number_of_ipsec_peers + 1):
    route_target = as_num + ':' + str(number + 2400)
    route_target_list.append(route_target)

service_set_list = [service_set_tmp for peer in range(1, number_of_ipsec_peers + 1)]

service_interface_list = []
for peer in service_interface_generator(number_of_ipsec_peers):
    service_interface_list.append(peer)

# from service_interface_list extract odd interfaces and assign to inside service interface
inside_service_interface_list = [odd_interfaces for odd_interfaces in service_interface_list[0::2]]
# from service_interface_list extract even interfaces and assign to outside service interface
outside_service_interface_list = [odd_interfaces for odd_interfaces in service_interface_list[1::2]]


ike_policy_list = [ike_policy for peer in range(1, number_of_ipsec_peers + 1)]
ipsec_policy_list = [ipsec_policy for peer in range(1, number_of_ipsec_peers + 1)]
instance_type_list = [instance_type for peer in range(1, number_of_ipsec_peers + 1)]
bgp_peer_as_num_list = [bgp_peer_as_num for peer in range(1, number_of_ipsec_peers + 1)]
# bgp_local_ipv4_address_list = [bgp_local_ipv4_address for peer in range(1, number_of_ipsec_peers + 1)]
# bgp_remote_ipv4_address_list = [bgp_remote_ipv4_address for peer in range(1, number_of_ipsec_peers + 1)]


# assert(number_of_ipsec_peers <= 255) #TODO figure out how to get number of subnets from base address for comparison

vrf_subnets_list = list(ipv4_vrf_peer_network_base.subnets(new_prefix=31))
assert(number_of_ipsec_peers <= len(vrf_subnets_list))

vrf_subnets_list = [vrf_subnets_list[x] for x in range(0, number_of_ipsec_peers)]

vrf_ipv4_subnet_hosts_list = []
for subnet in vrf_subnets_list:
    vrf_ipv4_subnet_hosts_list.append(ip_network(subnet).hosts())

hosts_per_subnet_list = []
for instance_local_gateway, instance_remote_gateway in vrf_ipv4_subnet_hosts_list:
    hosts_per_subnet_list.append((str(instance_local_gateway), str(instance_remote_gateway)))

instance_local_gateway_list = []
for address in hosts_per_subnet_list:
    instance_local_gateway_list.append(address[0])

instance_remote_gateway_list = []
for address in hosts_per_subnet_list:
    instance_remote_gateway_list.append(address[1])

# internal networks within ipsec tunnel

vrf_inside_subnets_list = list(ip4v_vrf_inside_network_base.subnets(new_prefix=31))
assert(number_of_ipsec_peers <= len(vrf_inside_subnets_list))

vrf_inside_subnets_list = [vrf_inside_subnets_list[x] for x in range(0, number_of_ipsec_peers)]

vrf_ipv4_inside_subnet_hosts_list = []
for subnet in vrf_inside_subnets_list:
    vrf_ipv4_inside_subnet_hosts_list.append(ip_network(subnet).hosts())

hosts_per_inside_subnet_list = []
for instance_inside_local_gateway, instance_inside_remote_gateway in vrf_ipv4_inside_subnet_hosts_list:
    hosts_per_inside_subnet_list.append((str(instance_inside_local_gateway), str(instance_inside_remote_gateway)))

instance_inside_local_gateway_list = []
for address in hosts_per_inside_subnet_list:
    instance_inside_local_gateway_list.append(address[0])

instance_inside_remote_gateway_list = []
for address in hosts_per_inside_subnet_list:
    instance_inside_remote_gateway_list.append(address[1])

bgp_local_ipv4_address_list = instance_inside_local_gateway_list
bgp_remote_ipv4_address_list = instance_inside_remote_gateway_list

data_set = zip(service_set_name_list, inside_service_interface_list, outside_service_interface_list,
               instance_local_gateway_list, instance_remote_gateway_list, instance_rule_name_list, ike_policy_list,
               ipsec_policy_list, instance_name_list, instance_type_list,
               route_distinquisher_list, route_target_list, bgp_local_ipv4_address_list, bgp_remote_ipv4_address_list)

data = []
# todo convert to named tuple and re-evaluate code
for entry in data_set:
    tmp = {}
    tmp['service_set_name'] = entry[0]
    tmp['inside_service_interface'] = entry[1]
    tmp['outside_service_interface'] = entry[2]
    tmp['instance_local_gateway'] = entry[3]
    tmp['instance_remote_gateway'] = entry[4]
    tmp['instance_rule_name'] = entry[5]
    tmp['ike_policy'] = entry[6]
    tmp['ipsec_policy'] = entry[7]
    tmp['instance_name'] = entry[8]
    tmp['instance_type'] = entry[9]
    tmp['route_distinguisher'] = entry[10]
    tmp['route_target'] = entry[11]
    tmp['bgp_local_ipv4_address'] = entry[12]
    tmp['bgp_remote_ipv4_address'] = entry[13]
    tmp['inside_service_int_ipv4_addr'] = entry[12]
    data.append(tmp)

# pprint(data)

template_loader = FileSystemLoader(searchpath="./")
template_env = Environment(loader=template_loader)
template_file = template_file
template = template_env.get_template(template_file)
result = template.render(routing_instance_list=data)

print(result)

with open(mx_output_file, 'w') as output_file:
    output_file.write(result)
