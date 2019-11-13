'''This script is to execute the shell level commands in an infinite loop. How to run the script# from a Ubuntu server running python3 
$ python3 --version
Python 3.4.3
$python3 <.pyfilename>, the script makes use of PYEZ juniper library'''
#!/usr/bin/env python3
'''This Script will repeadetly disable and enable interfaces'''
import time
from getpass import getpass
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
'''defining a function which will flap the interfaces'''
def flap_int(net_device):
        i=0
        while (i<1):
                print ("{} Connecting to {}".format(time.asctime(), net_device['ip']))
                junos_device = ConnectHandler(**net_device)
                configure = junos_device.config_mode()
                print ("{} Applying configuration to {}".format(time.asctime(), net_device['ip']))
                setssns = junos_device.send_command("set interfaces xe-0/0/0 disable") 
                print ("{} Committing configuration to {}".format(time.asctime(), net_device['ip']))
                junos_device.commit(comment='disabled interface')
                time.sleep(10)
                setssns = junos_device.send_command("delete interfaces xe-0/0/0 disable") 
                print ("{} Committing configuration to {}".format(time.asctime(), net_device['ip']))
                junos_device.commit(comment='Enabled interface', and_quit=True) 
                print ("{} Closing connection to {}".format(time.asctime(), net_device['ip']))
'''define a main function which will take the username and password and call the sub function flap_int'''
def main():
        user_login = input('Username: ') 
        user_pass = getpass('Password: ')
        with open('inventory.txt') as f: 
                device_list = f.read().splitlines()
                for device in device_list:
                        net_device = {
                        'device_type': 'juniper',
                        'ip': device,
                        'username': user_login,
                        'password': user_pass,
                        }
        flap_int(net_device)
if __name__ == '__main__':
   main()