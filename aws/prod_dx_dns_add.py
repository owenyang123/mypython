#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import dns
import os
import re
import getpass

dns_devices = []

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

username = getpass.getuser()
path = "/home/"+username

def extract_ip(device_name):
    for filename in os.listdir(path):
        if re.match(rf"console-log.+{device_name}.+.log", filename):
            with open(os.path.join(path, filename), 'r') as f:
                for line in f:
                    if re.search(r"vme.+ (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3})", line):
                        line_match = re.search(r"vme.+ (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3})",line)
                        vme_ip = line_match.group(1)
                        vme_ip, junk = vme_ip.split("/")
                        return vme_ip
                        break

dns_ip_list = []
username = getpass.getuser()
path = "/home/"+username


list_of_devices = input("provide the list of devices (comma separated): ")  # tuple variable which asks for multiple inputs
devices = list_of_devices.split(',')  # converts the contents of tuple into list items.


router_name = devices[0]  # Picking up the first item from devices list as router name
region = router_name[0:3]  # setting the region as first 3 characters from router name

pretend = input("Pretend or Add DNS entries [1 = pretend, 0 = add]: ")

for device in devices:
    device = device.replace(" ", "")
    print(bcolors.OKGREEN, device, bcolors.ENDC)
    ip_address = extract_ip(device)
    if (ip_address == None):
        print(bcolors.FAIL,"check console connection for {}".format(device),bcolors.ENDC)
        print(bcolors.FAIL,"check vme interface is up/up for {}".format(device),bcolors.ENDC)
    else:
        dns_ip_list.append(ip_address)
        dns_devices.append(device)

print(bcolors.WARNING,"adding DNS for {}".format(dns_devices),bcolors.ENDC)   
choice = input("Proceed to configure DNS[y/n]? ")
if choice.lower() == 'y':
    result = dns.dns_add_entries(region, dns_devices, dns_ip_list, pretend)
    if result:
        print(f"      {result}")
    else:
        print("      Error creating DNS entries.")
else:
    print(bcolors.OKGREEN,"exiting program...",bcolors.ENDC)
