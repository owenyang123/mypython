#!/usr/bin/python

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
from lxml import etree
from datetime import datetime
import yaml, argparse, jinja2
import time, logging, signal
import os, re, sys, warnings
import jnpr.junos.exception
import xml.etree.ElementTree as ET


parser = argparse.ArgumentParser()
parser.add_argument("host_info", type=argparse.FileType("r"), help="YAML based file containing managment IPs and user/password details.")
args = parser.parse_args()

sw_info = {}

def get_sw_info_function(host, username, password, role):
    host = host
    user = username
    passwd = password
    sw_info[host] = {}

    try:
        dev = Device(host = host, user = user, passwd = passwd)
        dev.open()
    except:
        print "Cannot connect to {}\n".format(host)
        print "Unable to verify existing Junos Version\n"
        raise SystemExit(1)

    dev.timeout = 300

    if role == "GNF" or role == "BSYS":
        get_sw_info = dev.rpc.cli('show version invoke-on all-routing-engines', format='xml')
        for re in get_sw_info.findall('multi-routing-engine-item'):
            sw_info[host][re.find('software-information/host-name').text] = re.find('software-information/junos-version').text
    if role == "JDM":
        get_sw_info = dev.rpc.cli('show version all-servers', format='xml', normalize = True)
        for re in get_sw_info.findall('multi-routing-engine-item'):
            seq = re.findtext('software-information/package-information[name="JDM package version"]/comment')
            version = seq.split(":")[-1]
            sw_info[host][re.findtext('software-information/host-name')] = version
    return sw_info

def main():
    host_file = args.host_info

    try:
        host_vars = yaml.load(host_file)
    except:
        print "\nUnable to load the input file. Please check syntax and Retry!!\n"
        print "Exiting...\n"
        raise SystemExit(1)
    # Copy the global variables in the input file to all routers
    for item in host_vars:
        for seq in range(len(host_vars['hosts'])):
            for host in host_vars['hosts'][seq]:
                if item != 'hosts':
                    if not host_vars['hosts'][seq][host].has_key(item):
                        host_vars['hosts'][seq][host][item] = host_vars[item]

    for entry in range(len(host_vars['hosts'])):
        for host in host_vars['hosts'][entry]:
            sw_info = get_sw_info_function(host, host_vars['hosts'][entry][host]['username'], host_vars['hosts'][entry][host]['password'], host_vars['hosts'][entry][host]['role'])

    #Print result
    for host in sw_info:
        for re in sw_info[host]:
            i = 0
            print("{} router: {} RE version: {} ".format(host, re, sw_info[host][re]))
            i += 1

if __name__ == '__main__':
    main()

