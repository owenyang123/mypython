#!/usr/bin/env python3

import argparse
import getpass
import logging
from jnpr.junos import Device
from jnpr.junos.exception import *
from jnpr.junos.utils.start_shell import StartShell
from concurrent.futures import ThreadPoolExecutor, as_completed
from lxml import etree


DEBUG = 0
DEF_NETCONF_CONCURRENT_SESSIONS = 10
DEF_NUM_CMD_ITERATIONS = 10
MIN_NUMBER_OF_THREADS = 5

show_bgp_sum = 'show bgp summary | match \
"(DirectConnection|peer-state|bgp-peer|bgp-rib|accepted-prefix-count)" | display xml'

show_version = 'show version brief | match Hostname '
show_int_lo0 = 'show interfaces lo0.100 terse | display xml '
show_bgp_sum_all = 'show bgp summary logical-systems PE-B-1 | match "^[0-9]" '
show_chassis_fpc = 'show chassis fpc detail | display xml '
show_route_engine = 'show chassis routing-engine | display xml '
show_int_media = 'show interfaces media | display xml '
show_ver_brief = 'show version brief | match Hostname '
show_sys_alarms = 'show system alarms | display xml '
show_sys_process= 'show system process extensive | display xml'


cmd_list = [show_bgp_sum, show_version, show_int_lo0, show_bgp_sum_all, show_chassis_fpc, show_route_engine,
            show_int_lo0, show_ver_brief, show_sys_alarms, show_sys_process]

#shell_cmd = 'cli -c "show task accounting"'

# set up logger
logger = logging.getLogger()

handler = logging.FileHandler('session-debug.log')
# change handler to item below to log to std.out rather than file
# handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description="Execute Junos CLI commands to isolate high CPU usage root cause")
parser.add_argument('hostname', help="hostname or management IPv4 address of Junos device")
parser.add_argument('-u', '--username',
                    help="username for authentication to device; default prompt user interactively")
parser.add_argument('-p', '--password',
                    help="password for authentication to device; default prompt user interactively")
parser.add_argument('-s', '--sessions', type=int,
                    help="number of concurrent executions (connections) made to DUT; default=1")
parser.add_argument('-i', '--iterations', type=int,
                    help="number of interactions of the command list to run per session to DUT; default=1")
args = parser.parse_args()


def print_device_info_banner(connection):

    """
    Prints out a formatted header with information obtained from the Juniper device.

    Args:
        connection: connection object for Juniper device; jnpr.junos.Device(host, user, passwd).open()

    Returns:
        A dictionary of lists containing each host address contained in each subnet. If no prefix_len
        argument is provided a dictionary containing a single list of all host addresses is returned.
        example:
            ================================================================================
            Connected to Host: jtac-MX240-r015_re0.ultralab.juniper.net
            Model: MX240
            Version: 11.4R12.4
            Serial Number: JN1245191AFC
            System has two routing-engines (current master): RE0
                RE Model: RE-S-1800x4
                Up Time: 8 hours, 4 minutes, 27 seconds
                Status: OK
            ================================================================================

    Raises:
        None.
    """
    seperator = '='
    width = 80
    print(seperator * width)
    print('Connected to Host: %s' % connection.facts['fqdn'])
    print('Model: %s' % connection.facts['model'])
    print('Version: %s' % connection.facts['version'])
    print('Serial Number: %s' % connection.facts['serialnumber'])

    if connection.facts['2RE']:
        print('System has two routing-engines (current master): %s' % connection.facts['master'])
        print('\tRE Model: %s' % connection.facts[connection.facts['master']]['model'])
        print('\tUp Time: %s' % connection.facts[connection.facts['master']]['up_time'])
        print('\tStatus: %s' % connection.facts[connection.facts['master']]['status'])
    else:
        print('System has single routing-engine: %s' % connection.facts['master'])
        print('\tRE Model: %s' % connection.facts['RE0']['model'])
        print('\tUp Time: %s' % connection.facts['RE0']['up_time'])
        print('\tStatus: %s' % connection.facts['RE0']['status'])
    print(seperator * width)

    return


def jnpr_device_connect(hostname, username, password, print_banner=False):

    """
    Connects to Juniper device using PyEZ jnpr.junos.Device(host, user, passwd).open(). If print_banner is
    True, a basic informational banner about the device is printed.

    Args:
        hostname: Juniper device hostname (fqdn) or IPv4 address.
        username: User name used for authentication to Juniper device.
        password: Password for authentication to Juniper device.
        print_banner: If true print device banner

    Returns:
        jnpr.junos.Device Connection Object

    Raises:
        ValueError: Raises an exception.
    """
    try:
        connection = Device(host=hostname, user=username, passwd=password).open()
        if print_banner:
            print_device_info_banner(connection)
        return connection
    except (ConnectTimeoutError, ConnectUnknownHostError, ConnectClosedError) as err:
        logger.debug('Connection error occurred: %s' % err)
        raise err
    except (ConnectAuthError, ConnectRefusedError) as err:
        logger.debug('Authentication or Firewall Filter error: %s' % err)
        raise err
    except ConnectError as err:
        logger.debug('Unknown Error occurred: %s' % err)
        raise err


def shell_exec(device_connection, command):
    with StartShell(device_connection) as sh:
        got = sh.run(command)
        ok = sh.last_ok
    return ok, got

if __name__ == '__main__':
    if args.username is None:
        args.username = getpass.getuser()
        logger.info('Username not provided on command-line using username: %s' % args.username)

    if args.password is None:
        args.password = getpass.getpass()

    if args.sessions is None:
        # if user didn't set number of concurrent sessions
        args.sessions = DEF_NETCONF_CONCURRENT_SESSIONS
        logger.info('Number of sessions not set on command-line, assuming %d sessions' % args.sessions)

    if args.iterations is None:
        # if user didn't set number of concurrent sessions
        args.iterations = DEF_NUM_CMD_ITERATIONS
        logger.info('Iterations not set on command-line, assuming %d iterations' % args.iterations)


    logger.info('Arguments: hostname=%s username=%s password=%s interval=%i' %
                (args.hostname, args.username, '********', args.sessions))

    def command_task(num, hostname, username, password):
        device_connection = jnpr_device_connect(hostname, username, password, print_banner=False)
        #device_connection.timeout = 180
        #status, result = shell_exec(device_connection, 'cli -c "set accounting on"')
        #print(result)
        for cmd in cmd_list:
            response = device_connection.cli(cmd, format='text', warning=False)
            #print(response)
            #print(etree.dump(response))
        #response = device_connection.rpc.get_route_information(logical_system='PE-B-1', table='bgp.l3vpn.0')

        #status, result = shell_exec(device_connection, shell_cmd)
        #print(result)

        device_connection.close()
        return num

    with ThreadPoolExecutor(max_workers=args.sessions) as executor:
        futures = []
        for thread_num in range(MIN_NUMBER_OF_THREADS, args.iterations + 1):
            futures.append(executor.submit(command_task, thread_num, args.hostname, args.username, args.password))

        for x in as_completed(futures):
            thread = x.result()
            print("Thread {} Completed".format(thread))
