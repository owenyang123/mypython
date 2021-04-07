# input the region and this program will return all the vc-cars and vc-cirs in region

#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import jukebox
import re

def sostenuto_devices_to_configure(region):
    sostenuto_devices = jukebox.get_devices_in_jukebox_region(region)

    vc_car_list = []
    vc_cir_list = []

    for device in sostenuto_devices:
        if 'cir' in device:
            vc_cir_list.append(device)
        elif 'car' in device:
            vc_car_list.append(device)

    return vc_car_list, vc_cir_list

vc_car_devices = []
vc_cir_devices = []
region = input("region: ")

vc_car_devices, vc_cir_devices = sostenuto_devices_to_configure(region)
