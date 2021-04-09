#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

# input a list of devices ex. iad12-vc-edg-r371,iad12-vc-edg-r372,etc
# os version, model number, serial number from JB is compared against NSM
# version: 1.0
# id: prakagan@

from dxd_tools_dev.modules import jukebox
from isd_tools_dev.modules import nsm

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
devices = jukebox.device_inventory(prod_dx_devices)

for device in devices:
    print("Autocheck being done for {}...".format(device.hostname))
    serial_number_jb = device.serial_number
    model_number_jb = device.model_number
    vme_interface_JB = device.loopback
    os_version_jb = device.os_version

    chassis_model_nsm, os_version_nsm, vme_interface_nsm, serial_number_nsm = device_info_from_nsm(device.hostname)

    try:
        if serial_number_jb.capitalize() != serial_number_nsm.capitalize():
            print("serial numbers from JB and the device do NOT match")
        elif vme_interface_JB != vme_interface_nsm:
            print("vme interface from JB and the device do NOT match")
        elif (os_version_jb.capitalize() != os_version_nsm.capitalize()):
            print("os version from JB and the device do NOT match")
        elif model_number_jb.capitalize() != chassis_model_nsm.capitalize():
            print("Model number from JB and the device do NOT match")
        else:
            print("serial numbers, model and os version from JB match devices - OK to proceed!")
    except AttributeError:
        print("check JUKEBOX to see if os version and model exists")
