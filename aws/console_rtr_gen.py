#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import sys
import os
import argparse
import logging
import yaml
import textwrap
import re
import pprint
import operator
import itertools
import ipaddr
import jinja2
from pyodinhttp import odin_retrieve, odin_material_retrieve, odin_retrieve_pair, OdinOperationError, OdinDaemonError

# from neteng_ndc import script_logging
import logging

logging.basicConfig(level=logging.INFO)

# pdq2-br-cpu-c1-oob-r1
# AZ = pdq2
# Fabric = br
# Layer = border_compute

IP_ADDRESS_REGEX = re.compile("^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$")

# Capture our current directory
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


# Helper Functions
def get_subnet_details(network):
    try:
        logging.debug('IP Subnet details for \'{}\': \n\tNetwork: {}\n\tNetMask: {}\n\t'
                     'PrefixLenght: {}\n\tHosts: {}'
                     .format(network, str(ipaddr.IPv4Network(network).network),
                             str(ipaddr.IPv4Network(network).netmask),
                             ipaddr.IPv4Network(network).prefixlen,
                             [str(host) for host in ipaddr.IPv4Network(network).iterhosts()]
                            ))
    except Exception as e:
        logging.error('{}'.format(e))
    return (str(ipaddr.IPv4Network(network).network),
            str(ipaddr.IPv4Network(network).netmask),
            ipaddr.IPv4Network(network).prefixlen,
            [str(host) for host in ipaddr.IPv4Network(network).iterhosts()])


def get_netmask(ip):
    logging.debug('IP and Mask details for \'{}\''
                  .format(ipaddr.IPv4Network(ip).with_netmask.split('/')))
    return ipaddr.IPv4Network(ip).with_netmask.split('/')


def emit_config(config):
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    logging.info('Loading Temaplte....')
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader('/apollo/env/DXDeploymentTools/templates/'),
                                undefined=jinja2.StrictUndefined)

    oob_template = 'oob_con_template.jt'

    template = j2_env.get_template(oob_template)
    logging.info('Template loaded successfully.... Template: {}'.format(oob_template))
    logging.info('Generating configuration....')
    # template = j2_env.Template(TEMPLATE, undefined=jinja2.StrictUndefined)
    template.globals['get_subnet_details'] = get_subnet_details
    template.globals['get_netmask'] = get_netmask
    template.globals['get_aws_secret_key'] = get_aws_secret_key
    return template.render(config)


def get_aws_secret_key(odin_material_name, show_password=False):
    try:
        if show_password:
            creds = odin_material_retrieve(_materialName=odin_material_name,
                                  _materialType="Credential")
            return creds
        creds = '<<'+odin_material_name+'>>'
    except OdinDaemonError as e:
        logging.error('{}'.format(e))
        creds = '<ERROR: UNABLE TO RETRIVE>'
    return creds


def parseArgs(args=sys.argv[1:]):
    "parses command line arguments"

    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
            This Script generates OOB Router Configuration for DX OOB devices.
            """),
        add_help=True,
    )
    parser.add_argument("-sc", "--show_credentials",
                        help="Use this to display passwords when config is generated",
                        action='store_true',
                        )

    parser.add_argument(
        "site_config",
        type=argparse.FileType('r'),
        help="the path to the config YAML file. E.g. cmh51-vc-con-oob.yaml",
    )
    config = parser.parse_args()
    return config


def load_yaml_data(config, fh):
    logging.info('Loading data from {}....'.format(fh))
    try:
        site_config = yaml.load(fh)
    except Exception as e:
        logging.error('{}'.format(e))
        SystemExit(1)
    # Load ALL Global vlaues
    config['global_config'] = {}
    for k, v in site_config['global'].items():
        config['global_config'][k] = v
    # Load OOB_ROUTERs and Setting Hostname list
    config['config_params'] = {}
    for k, v in site_config['oob_rtr'].items():
        config['config_params'][k] = v
    HOSTNAME_LIST = []
    HOSTNAME_LIST.append(config['config_params'].keys())
    config['names'] = sorted(HOSTNAME_LIST[0])
    for k, v in config['global_config'].items():
        print (k, " - ", v, "\n")
    print (config)
    return config





def main():
    # Get the arguements and parse them
    cli_args = parseArgs()

    config = {}
    print(cli_args.site_config)

    # Load yaml
    load_yaml_data(config, cli_args.site_config)
    if cli_args.show_credentials:
        config['show_creds'] = cli_args.show_credentials
    else:
        config['show_creds'] = False
    print ("after \n")
    print (config)
    print(emit_config(config))


if __name__ == '__main__':
    main()
