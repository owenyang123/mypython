#! /usr/bin/env python

"""
VPLS MAC STUCK Script. Use at your own risk.
    => Check only version. 

Ver 0.1
E. Schornig => eschornig@juniper.net
Date: 26.05.2016
"""

from RouterList import HL3_12 as HL3_12
from RouterList import HL3_11 as HL3_11
import logging
import jutil as JU
import time


logging.addLevelName(25, "_INFO_")
logging.basicConfig(format='%(asctime)s: %(module)s [%(funcName)s] [%(process)s] [%(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=25, filename='log.log')


class vpls_instance():
    def __init__(self):
        pass


class MPC():
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


def get_bd_index(dev, broken_instances):
    """
    Screen scrape to get BD_INDEX on PFE.
    """
    bd_index_list = JU.get_cli_cmd(dev, 'request pfe execute command "sh bridge-domain" target fpc1')
    for entry in bd_index_list.split('\n'):
        for instance in broken_instances:
            if instance.name in entry:
                entry = [x for x in entry.split(' ') if x != '']
                instance.bd_index = str(int(entry[2], 16))


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


def get_fpc_list(dev):
    """
    Will fetch the list of FPCs installed in the box along with the PFE numbers.
    """
    fpc_list = []
    logging.log(25, 'Looking for FPCs installed in [{}]'.format(dev.facts['hostname']))
    fpc_list_raw = JU.get_cli_cmd(dev, 'show chassis fpc', pipe=['Online']).split('\n')[:-1]
    for entry in fpc_list_raw:
        fpc = MPC()
        fpc.slot = [x for x in entry.split(' ') if x != ''][0]
        fpc.pfe_list = []
        logging.log(25, 'Detecting PFEs for FPCs installed in [{}]'.format(dev.facts['hostname']))
        cmd = 'request pfe execute command "sh jspec client" target fpc{}'.format(fpc.slot)
        pfe_list_raw = JU.get_cli_cmd(dev, cmd, pipe=['MQCHIP', 'XMCHIP']).split('\n')[:-1]
        for entry in pfe_list_raw:
            pfe = [x for x in entry.split(' ') if x != ''][2][-2:-1]
            fpc.pfe_list.append(pfe)
        fpc_list.append(fpc)
    return fpc_list


def get_hw_mac_list(dev, fpc_list, broken_instances):
    for fpc in fpc_list:
        for pfe in fpc.pfe_list:
            hw_mac_list = []
            cmd = 'request pfe execute command "sh l2metro {1} mac hw" target fpc{0}'.format(fpc.slot, pfe)
            hw_mac_raw = JU.get_cli_cmd(dev, cmd).split('\n')
            for entry in hw_mac_raw:
                mac = [x for x in entry.split(' ') if x != '']
                if len(mac) > 3:
                    hw_mac_list.append(mac)
            for instance in broken_instances:
                for mac in hw_mac_list:
                    if instance.bd_index == mac[1]:
                        if mac[3] not in instance.re_mac_list:
                            logging.error('Found stale MAC: [{0}] for instance [{1}] bd_index [{2}] on FPC: [{3}] PFE: [{4}]'.format(
                                mac[3], instance.name, instance.bd_index, fpc.slot, pfe))


def clear_vpls_mac_table(dev, broken_instances):
    cmd_list = []
    for instance in broken_instances:
        cmd = 'clear vpls mac-table instance {}'.format(instance.name)
        cmd_list.append(cmd)
    logging.error('Clearing mac table for broken instances.')
    JU.run_cli(dev, cmd_list)


def clear_all_vpls_macs(dev):
    logging.log(25, 'Clearing mac table for ALL instances.')
    JU.run_cli(dev, 'clear vpls mac-table')


def laser_off_100g(dev, hold_down):
    """
    Simple flap IFD command.
    """
    laser_off = 'cprod -A fpc2 -c "test cfp 1 laser off"'
    laser_on = 'cprod -A fpc2 -c "test cfp 1 laser on"'
    logging.log(25, 'Proceeding to power OFF laser for [et-2/0/0] on [{}] for [{}] seconds.'.format(dev.facts['hostname'], hold_down))
    JU.run_shell(dev, laser_off)
    time.sleep(hold_down)
    logging.log(25, 'Proceeding to power ON laser for [et-2/0/0] on [{}].'.format(dev.facts['hostname']))
    JU.run_shell(dev, laser_on)
    logging.log(25, 'Wait 120 seconds for things to settle down.')
    time.sleep(120)


def main():
    logging.log(25, '=' * 80)
    logging.log(25, 'Starting new check cycle!')
    logging.log(25, 'Will loop every 30 seconds until stuck MACs are found.')
    logging.log(25, '-' * 80)
    dev_list = [HL3_11, HL3_12]
    fault = False
    iteration = 1
    while fault is not True:
        print ' '
        logging.log(25, '-' * 80)
        logging.log(25, 'Test Iteration [{}].'.format(iteration))
        logging.log(25, '-' * 80)
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
                fpc_list = get_fpc_list(dev)
                get_bd_index(dev, broken_instances)
                get_re_mac_list(dev, broken_instances)
                get_hw_mac_list(dev, fpc_list, broken_instances)
                fault = True
            else:
                logging.log(25, 'Found no MAC stuck events on [{}]. Happy days!'.format(dev.facts['hostname']))
        print ' '
        iteration += 1
        if fault is not True:
            time.sleep(30)
        else:
            logging.log(25, 'Setup is in broken state. Use <vmc_clean.py> to clean up.')


if __name__ == '__main__':
    main()
