#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import re
import sys
import time
import logging
import argparse
import datetime
import subprocess
from pathlib import Path
from jinja2 import Template
from dxd_tools_dev.modules import nsm
from dxd_tools_dev.modules.utils import setup_logging


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HIGHGREEN = "\033[1;42m"

def parse_args():
    """Parse args input by user and help display"""
    parser = argparse.ArgumentParser(description='''Create var file and perform proper checkups for  edge group vc-edge turnup MCM \n
    wiki:TBD
    Examples:
    /apollo/env/DXDeploymentTools/bin/eg_turnup.py --edg 4 
    ''', add_help=True, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-g', '--edg', required=True, dest='edg', help='edge to be turned up')
    parser.add_argument('-b', '--ec2b', required=True, dest='ec2b', help='ex: bastion-dub8.ec2.amazon.com')
    parser.add_argument('-nb', '--ec2nb', required=True, dest='ec2nb', help='ex: neteng-bastion-ec2-dub8100.dub8-1.ec2.substrate')
    return parser.parse_args()

def get_bars_svc_goodies(device):
    try:
        data = nsm.get_device_interfaces_from_nsm(device)
        neig = []
        bars_inter_on_edg=[]
        neig_port=[]
        bar_port_combo = []
        check_neig_ports=[]
        for i in data:
            if 'Neighbor' in i:
                neig.append(i['Neighbor'])
                bars_inter_on_edg.append(i['Name'])
                neig_port.append(i['Neighbor_Port'])
                for j,bar in enumerate(neig):
                    for k,port in enumerate(neig_port):
                        if j == k:
                            w = bar + '_' + port
                            bar_port_combo.append(w)
        bars_inter_on_edg = list(dict.fromkeys(bars_inter_on_edg))
        bar_port_combo = list(dict.fromkeys(bar_port_combo))
        for i,port in enumerate(bars_inter_on_edg):
            for j, combo in enumerate(bar_port_combo):
                if i == j:
                    w = port + ':' + combo
                    check_neig_ports.append(w)
        neig = list(dict.fromkeys(neig))
        bars=[]
        svc=[]
        for i in neig:
            if 'bar' in i:
                bars.append(i)
            if 'svc' in i:
                i = i.replace('vc-svc','es-svc')
                svc.append(i)
        bars_dict = dict()
        bar_ip=[]
        for i,bar in enumerate(bars):
            ip = nsm.get_devices_detail_from_nsm(bar)[0][0]['IP_Address']
            bar_ip.append(ip)
            for j,ips in enumerate(bar_ip):
                if i == j:
                    bars_dict.update({bar:ips})
        return bars,svc,bars_dict,bars_inter_on_edg,[s for s in check_neig_ports if 'svc' not in s]
    except Exception as e:
        logging.error ( "Exception:get_bars_svc:{}".format ( str ( e ) ) )
        return None

def create_config(device,cfg_file):
    try:
        completed_process = subprocess.run ( '/apollo/env/HerculesConfigDownloader/bin/hercules-config --user-log-level critical get --hostname  {}  latest --file set-config --uncensored > {} '.format(device,cfg_file),shell=True,stdout=subprocess.PIPE)
        output = completed_process.stdout
        return output
    except Exception as e:
        log_error = "Could not get config info from Hercules of  {}".format ( device )
        logging.error ( log_error )
        logging.error ( e )
        sys.exit ()

def SCRAP_CFG_FILE(cfg_file, pattern):
    try:
        scrap = open ( cfg_file, "r" )
        regex = re.compile ( pattern )
        matched_config_lines = list ()
        for line in scrap:
            if regex.findall ( line ):
                matched_config_lines.append ( line )
        return (matched_config_lines)
        scrap.close ()

    except Exception as e:
        logging.error ( "Exception:SCRAP_CFG_FILE:{}".format ( str ( e ) ) )
        return None

def get_novice_prefix(cfg_file, pattern=r'(policy-options prefix-list VPC-VPN-NOVICE)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        match_NOVICE_PREFIX = str ( re.search ( r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/[2-3][0-9]$', get_line[ 0 ] ).group ( 0 ) )
        return match_NOVICE_PREFIX

    except Exception as e:
        logging.error ( "Exception:get_SOSV1_EG_IPV6_VARS:{}".format ( str ( e ) ) )
        return None

def get_region(device):
    try:
        region = nsm.get_devices_region_from_nsm(device)[0]['NSM_Stack']
        return region
    except Exception as e:
        logging.error ( "Exception:get_IPs_bars_edg:{}".format ( str ( e ) ) )
        return None

def var_file_creation(cfg_file,device,args_ec2b,args_ec2nb):
    rendered_var = home + '/{}_turnup.var'.format(device)
    var_file_temp = '''## set OS_VERSION = '17.2X75-D105.16'
## set REGION = '{{region}}'
## set EDG_NAME = '{{edg}}'
## set ES_SVC_PEER = '10.0.0.2'
## set ES_SVC_NAME = '{{svc}}'
## set NOVICE_PREFIX = '{{novice}}'
## set VCEDG_PEER = '10.0.0.3'
## set EC2_FABRIC_BASTION = '{{args_ec2b}}'
## set EC2_SSH_BASTION = '{{args_ec2nb}}'
## set TRANSPORT_NAME = '{{bars}}'
## set INTERFACES = '{{bars_interface_on_edg}}'
## set OPTIC_RX_LOW = -7.0
## set OPTIC_RX_HIGH = 2.0
## set TRAFFIC = '60'
## set PEER_IP = '{{bars_dict}}'
## set CONNECTIONS = '{{check_neig_ports}}'

{% raw %}
{% include 'brazil://DxVpnCMTemplates/templates/template_testing/edg_turnup2019.jt' %}
{% endraw %}'''
    logging.info ( "Fetching VC-BAR Parameter")
    bar_goodies = get_bars_svc_goodies(device)
    bars = bar_goodies[0]
    svc = bar_goodies[1][0]
    bars_dict = bar_goodies[2]
    bars_inter_on_edg = bar_goodies[3]
    check_neig_ports = bar_goodies[4]
    logging.info ( "Fetching VC-EDG Region")
    region = get_region(device)
    logging.info ( "Fetching VC-EDG NOVICE Prefix")
    create_config(device,cfg_file)
    novice_prefix = get_novice_prefix(cfg_file)
    logging.info ( "Generating VAR File for >> {}".format ( device ) )
    tm = Template ( var_file_temp )
    conf_file = tm.render ( region=region,edg=device,svc=svc,novice=novice_prefix,bars_interface_on_edg=bars_inter_on_edg,bars_dict=bars_dict,check_neig_ports=check_neig_ports,bars=bars,\
        args_ec2b=args_ec2b,args_ec2nb=args_ec2nb )
    rendered_config = open ( rendered_var, 'w+' )
    print ( conf_file, file=rendered_config )
    rendered_config.close ()

def main():
    now_time = datetime.datetime.now ()
    setup_logging ()
    global args
    global home
    global cfg_file
    args = parse_args ()
    device = args.edg
    home = str ( Path.home () )
    var_file = home + '/{}_turnup.var'.format(args.edg)
    cfg_file = home + "/edg.cfg"
    var_file_creation(cfg_file,device,args_ec2b=args.ec2b,args_ec2nb=args.ec2nb)
    print(
        bcolors.BOLD
        + 'VAR File saved in {}'.format(var_file)
        + bcolors.ENDC
    )
    finish_time = datetime.datetime.now ()
    duration = finish_time-now_time
    minutes, seconds = divmod(duration.seconds, 60)
    print("")
    print(bcolors.UNDERLINE + "Script Time Stats:" + bcolors.ENDC)
    print(
        bcolors.WARNING
        + "The script took {} minutes and {} seconds to run.".format(minutes, seconds)
        + bcolors.ENDC
    )

if __name__ == "__main__":
        main()


