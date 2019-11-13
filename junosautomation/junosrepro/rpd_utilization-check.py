#!/usr/bin/env python

import argparse
from datetime import datetime
import re
import paramiko
import yaml


parser = argparse.ArgumentParser()
parser.add_argument("host_info", type=argparse.FileType("r"), help="YAML based file containing managment IPs and user/password details.")
args = parser.parse_args()


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

    print "Date,      Time,     Hostname,       Platform,   Junos,      RPD MEM,   RPD CPU"
    for entry in range(len(host_vars['hosts'])):
        for host in host_vars['hosts'][entry]:
            if host_vars['hosts'][entry][host]['role'] == "GNF" or  host_vars['hosts'][entry][host]['role'] == "BSYS":
                get_rpd_utilization(host, host_vars['hosts'][entry][host]['username'], host_vars['hosts'][entry][host]['password'], host_vars['hosts'][entry][host]['role'])


def get_rpd_utilization(host, username, password, role):
    host = host
    user = username
    passwd = password
    role = role

    try:
        dev = paramiko.SSHClient()
        dev.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        dev.connect(host, username=user, password=passwd, look_for_keys=False, allow_agent=False)
    except:
        print "Cannot connect to {}\n".format(host)
        print "Unable to verify existing Junos Version\n"
        raise SystemExit(1)

    if role == "GNF" or role == "BSYS":
        stdin, stdout, stderr = dev.exec_command('show version')
        show_ver = stdout.readlines()
        for item in show_ver:
            if 'Hostname' in item:
                hostname = re.search(r':.*',item).group(0)[2:]
            elif 'Model' in item:
                platform = re.search(r':.*',item).group(0)[2:]
            elif 'Junos:' in item:
                junos = item[7:]
        stdin, stdout, stderr = dev.exec_command('show system processes extensive | match rpd')
        rpd_check = stdout.readlines()
        for line in rpd_check:
            rpdcpu = line.split()[10]
            rpdmem = line.split()[5]
        timeanddate = str(datetime.now())
        time = timeanddate[11:19]
        date = timeanddate[0:10]
        print "{}, {},  {},  {}, {},  {},  {}".format(date,time,hostname,platform,junos.strip(),rpdmem,rpdcpu)
        dev.close()

if __name__ == '__main__':
    main()
