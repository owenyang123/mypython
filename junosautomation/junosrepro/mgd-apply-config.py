#!/usr/bin/python
#
# Author: Ryan Barnes [barnesry@juniper.net]
# Date  :    June 7, 2017
#
# Description:
#   Add/remove configuration from MX using private mode.
#   Generate a unique UUID for each run, specifying a present MS-MPC and VT (tunnel) interface for the target chassis
#   Generate the configuration from .j2 template, apply the config, wait X seconds, remove the config, rinse, repeat.
#
# USAGE:
#   barnesry-mbp$ ./mgd-apply-config.py --host 10.13.110.166 --user barnesry --mpc ms-0/0/0 --vt vt-2/0/0
#
# Version History
#   0.1     June 7, 2017

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
from lxml import etree as etree
from collections import defaultdict
import argparse, logging, getpass
import time, os
import uuid
import jinja2
import sys
import random


def get_mpc_unit(seed):
    # return some value in the 2k range for inside interfaces
    # return some value in the 4k range for outside interfaces
    return random.randrange(seed, seed+999, 1)

def render(tpl_path, context):
    ''' renders our configuration from template '''
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def apply_configuration(dev, config_text):
    ''' applies config to the device '''

    # Lock the configuration, load configuration changes, and commit
    # print "Locking the configuration"
    # try:
    #     dev.cu.lock()
    # except LockError:
    #     print "Error: Unable to lock configuration"
    #     dev.close()
    #     return

    print "Loading configuration changes"
    try:
        
        dev.cu.load(config_text, format="text", merge=True, mode="private")
    except ValueError as err:
        print err.message

    except RpcError as err:
        print err
        if err.rsp.find('.//ok') is None:
            rpc_msg = err.rsp.findtext('.//error-message')
            print "Unable to load configuration changes: ", rpc_msg

        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        dev.close()
        sys.exit()
        return

    # show the diff
    #dev.cu.pdiff()

    print "Committing the configuration"
    try:
        dev.cu.commit(timeout=360)
    except CommitError as err:
        print "Error: Unable to commit configuration"
        print err.rsp
        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        dev.close()
        sys.exit()
        return

    # print "Unlocking the configuration"
    # try:
    #     dev.cu.unlock()
    # except UnlockError:
    #     print "Error: Unable to unlock configuration"

def get_customer_info(cust_id, cust_table):
    ''' iterate customer ID and UUID and write to hash '''
    cust_id = cust_id + 1
    cust_table[cust_id] = str(uuid.uuid4())

    return cust_table

def main(args):

    add_config_template = 'add_customer_config.j2'
    del_config_template = 'delete_customer_config.j2'

    host = args.host
    user = args.user
    #password = args.password
    if args.mpc:
        mpc = args.mpc
    else:
        mpc = "ms-0/0/0"

    if args.vt:
        vt = args.vt
    else:
        vt = 'vt-0/0/0'

    time_sleep =30

    cust_id = 2000    # seed customer_id
    cust_table = {}

    # connect to our device
    with Device(host=host, user=user) as dev:
        print "Connecting to...{}".format(dev.hostname)
        dev.open()
        dev.timeout = 300
        print "Success!"

        # bind the config to our dev object
        dev.bind(cu=Config)


        while cust_id < 2500:


            # generate the customer info
            cust_table[cust_id] = str(uuid.uuid4())
            print "Customer {} : {}".format(cust_id, cust_table[cust_id])

            mpc_inside_unit = get_mpc_unit(2000)
            mpc_outside_unit = get_mpc_unit(4000)

            # generate the context we can pass to our template
            context = {'cust_id' : cust_id,
                       'uuid' : cust_table[cust_id],
                       'mpc' : mpc,
                       'vt' : vt,
                       'mpc_inside_unit' : mpc_inside_unit,
                       'mpc_outside_unit' : mpc_outside_unit}
            config_text = render(add_config_template, context)
            print config_text

            print "Adding config..."
            apply_configuration(dev, config_text)

            print "Sleeping for {}sec".format(time_sleep)
            time.sleep(time_sleep)

            print "Removing config..."
            config_text = render(del_config_template, context)
            #print config_text

            apply_configuration(dev, config_text)

            print "Sleeping for {}sec".format(time_sleep)
            time.sleep(time_sleep)

            sys.stdout.flush()
            cust_id += 1

        # End the NETCONF session and close the connection
        dev.close()

# executes only if not called as a module
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="host", help="target for connection", required=True)
    parser.add_argument("--user", dest="user", help="username to connect with", required=False)
    parser.add_argument("--mpc", dest="mpc", help="defaults to ms-0/0/0", required=False)
    parser.add_argument("--vt", dest="vt", help="defaults to vt-0/0/0", required=False)
    args = parser.parse_args()

    #password = getpass.getpass()
    #args.password = password

    # Change ERROR to INFO or DEBUG for more verbosity
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    # run our main program
    main(args)
