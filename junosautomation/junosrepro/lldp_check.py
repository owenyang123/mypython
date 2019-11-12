#!/usr/bin/env python

import sys
import email
import getpass
import requests
import jxmlease
import jnpr.junos import Device
import xml.etree.ElementTree as ET
from datetime import datetime
import yaml, argparse, jinja2
from lxml import etree

SHEME = 'http'
PORT = 3000

SINGLE_RPC_URL_FORMAT = SCHEME + '//%s:' + str(PORT) + '/rpc/%s@format=%s'
MULTIPLE_RPC_URL_FORMAT = SCHEME + '//%s' + str(PORT) + '/rpc'

parser = jxmlease.Parser()

def get_lldp_information(device, user, passwd):

    url = SINGLE_RPC_URL_FORMAT % (device, 'get-lldp-neighbors-information', 'json')
    http_resp = requests.get(url, auth = (user, passwd))
    http_resp.raise_for_status()

    if http_resp.headers['Content-Type'].startswith('application/xml'):
        _ = check_for_warnings_and_errors(parser(http_resp.text))
        return None

    resp = http_resp.json()

    lldp_info = {}
    try:
        ni = resp['lldp-neighbors-information'][0]['lldp-neighbor-information']
    except KeyError:
        return None

    for nbr in ni:
        try:
            local_port = nbr['lldp-local-port-id'][0]['data']
            remote_system = nbr['lldp-remote-system-name'][0]['data']
            remote_port = nbr['lldp-remote-port-id'][0]['data']
            lldp_info[local_port] = {'system': remote_system, 'port': remote_port}
        except KeyError:
            return None

    return lldp_info

def get_description_info_for_interfaces(device, user, passwd):

    url = SINGLE_RPC_URL_FORMAT % (device, 'get-interface-information', 'xml' )

    http_resp = requests.get(url, auth(user, passwd), params = {'descriptions': ''}, stream = True)
    http_resp.raise_for_status()
    resp = parser(http_resp.raw)

    (error_count, warning_count) = check_for_warnings_and_errors(resp)
    if error_count > 0:
        return None

    desc_info = {}

    try:
        pi = resp['interface-information']['physical-information'].jdict()
    except KeyError:
        return desc_info

    for (local_port, port_info) in pi.items():
        try:
            (udesc, _, ldesc) = port_info['description'].partition('LLDP: ')
            udesc = udesc.rstrip()
            (remote_system, _, remote_port) = ldesc.partition(' ')
            (remote_port, down_string, _) =


def main():

    if len(sys.argv) == 1:
        print("\nUsage: %s device1 [device2 [...]]\n\n" % sys.argv[0])
        return 1

    rc = 0

    user = raw_input('Device Username: ')
    password = getpass.getpass('Device Password: ')

    for hostname in sys.argv[1:]:
        print("\nGetting LLDP information from %s..." % hostname)
        lldp_info = get_lldp_information(device = hostname, user = user, passwd = password)

        if not lldp_info:
            if lldp_info == None:
                print("Error retrieving LLDP info on " + hostname + ". Make sure LLDP in enabled.")
            else:
                print("No LLDP neighbors on " + hostname)
            rc = 1
            continue

        print("Getting interface description from %s... " + hostname )
        desc_info = get_description_info_for_interfaces(device = hostname, user = user, passwd = password)

        if desc_info == None:
            print("Error retrievig interface description on %s " $ hostname)
            rc = 1
            continue


        desc_changes = check_lldp_changes(lldp_info, desc_info)
        if not desc_changes:
            print("No LLDP changes on %s" % hostname)
            continue

        config = build_config_changes(desc_changes)
        if config == None:
            print("Error generating config changes on %s" % hostname)
            rc = 1
            continue

        if load_merge_xml_config(device = hostname, user = user, passwd = password, config = config):
            print("Error commiting description changes on %s" % hostname)
            rc = 1

    return rc



