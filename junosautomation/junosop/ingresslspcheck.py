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
    try:os.mkdir("/var/tmp/script_outputs")
    except:print('Script Directory already existed')
    cli_arguments = parse_args()
    lsp_name=cli_arguments.lsp_name
    with open(os.devnull, 'wb') as DEVNULL:
        completed_process = subprocess.run('cli -c "show configuration protocols bgp |display inheritance no-comments  | match local-address"', shell=True, stdout=subprocess.PIPE, stderr=DEVNULL)
        config =[i[-14:-1] for i in list(set(completed_process.stdout.decode('ascii').split("\n"))) if i!=""]
        cmd='cli -c'+" "+'\''+'show configuration protocols mpls label-switched-path {}'.format(lsp_name)+'|match \"to \"' +'\''
        completed_process = subprocess.run(cmd,shell=True, stdout=subprocess.PIPE, stderr=DEVNULL)
        RSVP_SESSION_NEIGHBOR=completed_process.stdout.decode('ascii').split(",")[0].split(" ")[1][:-2]

if __name__ == '__main__':
    main()