#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

# input a list of devices ex. iad12-vc-edg-r371,iad12-vc-edg-r372,etc
# os version, model number, serial number from JB is compared against NSM
# version: 1.0
# id: prakagan@

from dxd_tools_dev.modules import jukebox
from isd_tools_dev.modules import nsm


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

def device_info_from_nsm(hostname):
    device_info = nsm.get_raw_hardware_for_device(hostname)
    for part in device_info['hardware']:
        if (part['hardware_name'] == 'Chassis'):
            serial_number_nsm = part['serial_number']

    chassis_model_nsm = device_info['chassis_model']
    os_version_nsm = device_info['software']['version']

    #vme_interface_nsm = device_info['connectivity']['reachable_interfaces'][0]['interface_ip']

    vme_interface_nsm = device_info['connectivity']['ipv4_addresses'][0]


    return(chassis_model_nsm, os_version_nsm, vme_interface_nsm, serial_number_nsm)


prod_dx_devices = input("input list of devices (ex. iad12-vc-edg-r201,iad12-vc-edg-r202):")
try:    
    devices = jukebox.device_inventory(prod_dx_devices)
except TypeError:
    print(bcolors.HEADER, "Device does not exist in JB or you need to poll the devices in NSM\n", bcolors.ENDC)

for device in devices:
    print(bcolors.HEADER,"Autocheck being done for {}...".format(device.hostname),bcolors.ENDC)
    serial_number_jb = device.serial_number
    model_number_jb = device.model_number
    vme_interface_JB = device.loopback
    os_version_jb = device.os_version

    chassis_model_nsm, os_version_nsm, vme_interface_nsm, serial_number_nsm = device_info_from_nsm(device.hostname)

    try:
        if serial_number_jb.capitalize() != serial_number_nsm.capitalize():
            print(bcolors.FAIL,"serial numbers from JB and the device do NOT match",bcolors.ENDC)
        elif vme_interface_JB != vme_interface_nsm:
            print(bcolors.FAIL,"vme interface from JB and the device do NOT match",bcolors.ENDC)
        elif (os_version_jb.capitalize() != os_version_nsm.capitalize()):
            print(bcolors.FAIL,"os version from JB and the device do NOT match",bcolors.ENDC)
        elif model_number_jb.capitalize() != chassis_model_nsm.capitalize():
            print(bcolors.FAIL,"Model number from JB and the device do NOT match",bcolors.ENDC)
        else:
            print(bcolors.OKGREEN,"serial numbers, model and os version from JB match devices - OK to proceed!", bcolors.ENDC)
    except AttributeError:
        print(bcolors.FAIL,"os version or model number from JB and device do NOT match",bcolors.ENDC)
