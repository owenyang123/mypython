#! /usr/bin/env python

"""
VPLS MAC STUCK Script. Use at your own risk.

Ver 0.1
E. Schornig => eschornig@juniper.net
Date: 26.05.2016
"""

from RouterList import HL3_12 as HL3_12
from RouterList import HL3_11 as HL3_11
import logging
from pprint import pprint as pp
import jutil as JU
import time
import sys


logging.addLevelName(25, "_INFO_")
logging.basicConfig(format='%(asctime)s: %(module)s [%(funcName)s] [%(process)s] [%(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=25, filename='log.log')


class vpls_instance():
    def __init__(self):
        pass


def get_vpls_broken(dev, mac_count=20):
    """
    Checks for any instances where not all macs are learned on RE side.
    """
    stats = JU.get_cli_cmd(dev, 'show vpls mac-table count',
                           pipe=['MAC address learned in routing instance VPLS_BASIC_11']).split('\n')[:-1]
    broken_instances = []
    for entry in stats:
        shards = entry.split(' ')
        if int(shards[0]) == 0:
            inst = vpls_instance()
            inst.name = shards[7]
            logging.error('Found no MACs in instance: [].'.format(inst.name))
        elif int(shards[0]) < mac_count:
            inst = vpls_instance()
            inst.name = shards[7]
            inst.re_mac = shards[0]
            logging.error('Found broken instance [{}]: MAC Count [{}] out of [{}].'.format(
                inst.name, inst.re_mac, mac_count))
            broken_instances.append(inst)
        elif int(shards[0]) > mac_count:
            inst = vpls_instance()
            inst.name = shards[7]
            inst.re_mac = shards[0]
            logging.error('To many MACs in instance [{}]: MAC Count [{}] out of [{}].'.format(
                inst.name, inst.re_mac, mac_count))
            broken_instances.append(inst)
    return broken_instances


def get_re_mac_list(dev, broken_instances):
    """
    Will fetch the list of MACs learned on RE.
    """
    for instance in broken_instances:
        mac_list_raw = JU.get_cli_cmd(dev, 'show vpls mac-table instance {}'.format(instance.name),
                                      pipe=['lsi.']).split('\n')[:-1]
        instance.re_mac_list = []
        for entry in mac_list_raw:
            mac = [x for x in entry.split(' ') if x != ''][0]
            instance.re_mac_list.append(mac)


def clear_vpls_mac_table(dev, broken_instances):
    cmd_list = []
    for instance in broken_instances:
        cmd = 'clear vpls mac-table instance {}'.format(instance.name)
        cmd_list.append(cmd)
    logging.error('Clearing mac table for broken instances.')
    JU.run_cli(dev, cmd_list)


def main():
    logging.log(25, 'Running <clean> mode. Will clean any stale MACs in the setup.')
    dev_list = [HL3_11, HL3_12]
    for router in dev_list:
        print ' '
        dev = JU.connect(router['mgmt'],
                         user='eschornig',
                         password='lab123',
                         facts=False)
        logging.log(25, 'Connected to [{}]. Checking for trouble.'.format(dev.facts['hostname']))
        logging.log(25, '-' * 80)
        broken_instances = get_vpls_broken(dev)
        if len(broken_instances) > 0:
            # If we are broken, let's clean up.
            logging.error('Found broken instances!')
            logging.error('Procceding to clear mac table for broken instances.')
            clear_vpls_mac_table(dev, broken_instances)
        else:
            logging.log(25, 'Found no MAC stuck events on [{}]. Happy days!'.format(dev.facts['hostname']))


if __name__ == '__main__':
    main()
