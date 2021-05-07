from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell
from datetime import datetime as t
import subprocess
import argparse
import os
import re

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='lspcheck.py')
    main_parser.add_argument("-l", "--lsp", type=str, dest="lsp_name", required=True, help="Comma separated names of LSPs")
    return main_parser.parse_args()

def main():
        cli_arguments = parse_args()
        print(cli_arguments.lsp_name)
        return

if __name__ == '__main__':
        main()
