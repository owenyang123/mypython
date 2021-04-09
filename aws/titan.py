#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from dxd_tools_dev.modules import jukebox
from dxd_tools_dev.datastore import ddb
import pandas as pd
import xlwt
import subprocess
import argparse
import string
import random
import sys
import time
import datetime
import re

'''
Script Usage:
network-config-builder-12004.dub2$ brazil-runtime-exec python3 bin/titan.py --help
usage: titan.py [-h] -pr -fegp  

Script to perform Titan deployment subtasks

optional arguments:
  -h, --help         show this help message and exit
  -pr , --parent-region      Parent AZ to which Titan will be homed.
  -fegp , --find-edg-groups  Find Commercial Edge groups in parent region.
'''

    
def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Script to perform Titan deployment subtasks ")
    parser.add_argument('-az','--parent_az', type=str, metavar = '', required= True, help = 'Parent AZ to which Titan will be homed')
    parser.add_argument('-fegp','--find-edg-groups',action="store_true",help="Find Commercial Edge groups in parent region.")
    return parser.parse_args()
 
def find_edg_groups(args):
    '''This function finds commercial edg groups in parent az using JukeBox'''
    edg_grp = list()
    az = args.parent_az
    d = jukebox.get_site_region_details(az)
    for x in d.region.edg_groups:
        if 'ExternalCustomer' == x.edg_group_type:
            edg_grp.append(x.id)
    print (f"All commercial Edg groups in {args.parent_az}:", edg_grp)
    print (f"Total number of Commercial edg groups in {args.parent_az}:", len(edg_grp))

def main():
    args = parse_args()
    if args.find_edg_groups:
        find_edg_groups(args)
    else:
        print("Error : Please provide Valid Arguments")
        sys.exit()

if __name__ == "__main__":
    main()
