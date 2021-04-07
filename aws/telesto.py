#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import sys
import os
import argparse
import logging

from dxd_tools_dev.modules.telesto import create_cutsheet_mcm

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='telesto.py', description='DX2.0 Deployment tool')
    subparsers = main_parser.add_subparsers(help='commands', dest='command')

    cutsheet_parser = subparsers.add_parser('cutsheet', help='Create cutsheet for dx2.0 deployment')
    cutsheet_parser.add_argument("-r", "--region", action="store", dest="region", required=True, help="parent region for dx pop site e.g iad, dub,sin")
    cutsheet_parser.add_argument("-s", "--dx_site", action="store",  dest="dx_site", required=True, help="site for deployment e.g iad66")
    cutsheet_parser.add_argument("-b", "--brick_num", action="store", dest="brick_num", required=True, help="dx2.0 brick number e.g 1")
    cutsheet_parser.add_argument("-bp", "--border_pops", action="store", nargs='+', dest="border_pops", required=True, help="border sites separated by space e.h iad79 iad89")

    return main_parser.parse_args()




def gen_cutsheet():
    cli_arguments = parse_args()
    region = cli_arguments.region
    dx_pop = cli_arguments.dx_site
    telesto_brick = cli_arguments.brick_num
    border_pops = cli_arguments.border_pops

    create_cutsheet_mcm(region, dx_pop,telesto_brick, border_pops)


def main():
    gen_cutsheet()


if __name__ == '__main__':
    main()
