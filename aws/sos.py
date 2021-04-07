#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import os
import re
import git
import sys
import math
import getpass
import logging
import argparse
import datetime
import subprocess
from pathlib import Path
from jinja2 import Template
from dxd_tools_dev.modules.utils import setup_logging
from dxd_tools_dev.modules import jukebox,mcm

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
    parser = argparse.ArgumentParser(description='''Create conf and diff files for new edge group Sostenuto setup\n
    wiki:TBD
    Examples:
    /apollo/env/DXDeploymentTools/bin/sos.py --GN 4 --region nrt -m 6
    ''', add_help=True, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-g', '--GN', required=True, dest='GN', help='New Edge Group Number')
    parser.add_argument('-r', '--region',  required=True, dest='region', help='region code iad,dub,nrt,.....')
    parser.add_argument("-m", "--max_per_MCM", default=4, type=int, dest="max_per_MCM", help="Maximum number of CAR devices per MCM. Default: 4")
    return parser.parse_args()

def validate_input(args):
    logging.info ( 'Valdating input' )
    if int(args.GN) not in range(1,11,1):
        logging.error("out of supported group range")
        exit()
    if args.region not in ['iad', 'pdx', 'bjs', 'fra', 'bom', 'hkg', 'nrt', 'cmh', 'arn', 'dub','syd', 'lhr', 'pek', 'yul', 'kix', 'corp', 'cdg', 'bah', 'zhy', 'sfo',\
                           'sin', 'icn', 'gru', 'cpt', 'mxp']:
        logging.error("Unsupported Region")
        exit()

def sostenuto_devices_to_configure(region):
    sostenuto_devices = jukebox.get_devices_in_jukebox_region(region)
    vc_car_list = []
    vc_cir_list = []
    for device in sostenuto_devices:
        if 'cir' in device:
            vc_cir_list.append(device)
        elif 'car' in device:
            vc_car_list.append(device)
    regex = re.compile ( r'-p[1-9]-v[1-9]' )
    vc_car_list = [ i for i in vc_car_list if not regex.search ( i ) ]
    return vc_car_list, vc_cir_list

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

def get_SOSV1_EG_IPV6_VARS(cfg_file,GN, pattern=r'(TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-1)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        match_IPV6_PREFIX = re.search ( r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4})\
        {1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:\
        ((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}\
        (25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))',get_line[ 0 ] ).group ( 1 )
        SOSV1_EG_IPV6_PREFIX = match_IPV6_PREFIX[ :-2 ]+str ( int ( GN ) * 10 )+"/125"
        SOSV1_EG_IPV6_CUSTIP = match_IPV6_PREFIX[ :-2 ]+str ( int ( GN ) * 10+6 )+"/125"
        SOSV1_EG_IPV6_NEIG = match_IPV6_PREFIX[ :-2 ]+str ( int ( GN ) * 10+1 )
        SOSV1_EG1_IPV6_NEIG = match_IPV6_PREFIX[:-2]+str (11)
        return SOSV1_EG_IPV6_NEIG, SOSV1_EG_IPV6_CUSTIP, SOSV1_EG_IPV6_PREFIX,SOSV1_EG1_IPV6_NEIG

    except Exception as e:
        logging.error ( "Exception:get_SOSV1_EG_IPV6_VARS:{}".format ( str ( e ) ) )
        return None

def get_SOSV1_EG_IPV4_VARS(cfg_file,GN, pattern=r'(TESTLOOP-1-PRIVATE-EDGGROUP-1)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        match_IPV4_PREFIX = str ( re.search ( r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', get_line[ 0 ] ).group ( 0 ) )
        SOSV1_EG_PREFIX = match_IPV4_PREFIX[ :-3 ]+str ( 4 * (int ( GN )-1)+100 )+"/30"
        SOSV1_EG_CUSTIP = match_IPV4_PREFIX[ :-3 ]+str ( 4 * (int ( GN )-1)+102 )+"/30"
        SOSV1_EG_NEIG = match_IPV4_PREFIX[ :-3 ]+str ( 4 * (int ( GN )-1)+101 )
        SOSV1_EG1_IPV4_NEIG = match_IPV4_PREFIX[:-3]+str (101)
        SOSV1_AMAZON_IP_EG1 = match_IPV4_PREFIX[ :-3 ]+ str ( 101 ) +"/30"
        return SOSV1_EG_NEIG, SOSV1_EG_CUSTIP, SOSV1_EG_PREFIX,SOSV1_EG1_IPV4_NEIG,SOSV1_AMAZON_IP_EG1

    except Exception as e:
        logging.error ( "Exception:get_SOSV1_EG_IPV4_VARS: {}".format ( str ( e ) ) )
        return None

def get_VLAN_for_IPv4(GN):
    start_VLAN = "100"
    SOSV1_EG_VLAN = int ( start_VLAN )+(int ( GN )-1) * 4
    return SOSV1_EG_VLAN

def get_VLAN_for_IPv6(GN):
    start_VLAN = "600"
    SOSV1_EG_IPV6_VLAN = int ( start_VLAN )+(int ( GN )-1) * 4
    return SOSV1_EG_IPV6_VLAN

def get_SOSV1_CUST_INT(cfg_file, GN, pattern=r'(routing-instances TESTLOOP-1-PRIVATE-EDGGROUP-1 interface)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        SOSV1_CUST_INT = re.search ( r'(ge-|xe-|et-)\d{1,2}\/\d{1,2}\/\d{1,2}', get_line[ 0 ] ).group ( 0 )
        return SOSV1_CUST_INT

    except Exception as e:
        logging.error ( "Exception:get_SOSV1_CUST_INT: {}".format ( str ( e ) ) )
        return None

def get_SOSV1_RID(cfg_file,GN, pattern=r'(TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-1 routing-options router-id)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        SOSV1_RID = str ( re.search ( r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', get_line[ 0 ] ).group ( 0 ) )
        return SOSV1_RID

    except Exception as e:
        logging.error ( "Exception::get_SOSV1_RID: {}".format ( str ( e ) ) )
        return None

def get_SOSV1_PEERAS(cfg_file,GN):
    try:
        EG1_IPV6_PREFIX = get_SOSV1_EG_IPV6_VARS(cfg_file,GN)[3]
        pattern = r'(set routing-instances TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-1 protocols bgp group ebgp neighbor {} peer-as)'.format(EG1_IPV6_PREFIX)
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        SOSV1_PEERAS = re.search(r'\b\d{4}\b$|\b\d{5}\b$',get_line[0]).group(0)
        return SOSV1_PEERAS

    except Exception as e:
        logging.error ( "Exception:get_SOSV1_PEERAS: {}".format ( str ( e ) ) )
        return None

def get_SOSV1_PEERAS_CIR(cfg_file,GN):
    try:
        EG1_IPV4_PREFIX = get_SOSV1_EG_IPV4_VARS(cfg_file,GN)[3]
        pattern = r'(set routing-instances TESTLOOP-1-PRIVATE-EDGGROUP-1 protocols bgp group ebgp neighbor {} peer-as)'.format(EG1_IPV4_PREFIX)
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        SOSV1_PEERAS = re.search(r'\b\d{4}\b$|\b\d{5}\b$',get_line[0]).group(0)
        return SOSV1_PEERAS

    except Exception as e:
        logging.error ( "Exception:get_SOSV1_PEERAS_CIR: {}".format ( str ( e ) ) )
        return None

def get_SOSV1_AUTH_KEY(cfg_file,GN):
    try:
        EG1_IPV4_PREFIX = get_SOSV1_EG_IPV4_VARS(cfg_file,GN)[3]
        pattern = r'(set routing-instances TESTLOOP-1-PRIVATE-EDGGROUP-1 protocols bgp group ebgp neighbor {} authentication-key)'.format(EG1_IPV4_PREFIX)
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        SOSV1_AUTH_KEY = re.search(r'"(.*?)"$',get_line[0]).group(0)
        return SOSV1_AUTH_KEY
    except Exception as e:
        logging.error ( "Exception:SOSV1_AUTH_KEY: {}".format ( str ( e ) ) )
        return None

def get_SOSV1_1st_deployed_car(cfg_file, pattern=r'(TESTLOOP-1-DX-VPN-DATA-PLANE)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        if get_line:
            return True
        else:
            return False
    except Exception as e:
        logging.error ( "Exception:get_SOSV1_1st_deployed_car: {}".format ( str ( e ) ) )
        return None

def get_SOSV1_DX_VPN_3rd_OCTET(cfg_file, pattern=r'(TESTLOOP-1-DX-VPN-DATA-PLANE-ADVERTISEMENT)'):
    try:
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        match_IPV4_PREFIX = str ( re.search ( r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', get_line[ 0 ] ).group ( 0 ) )
        SOSV1_DX_VPN_3rd_octet= match_IPV4_PREFIX[ :-3 ]
        if SOSV1_DX_VPN_3rd_octet:
            return SOSV1_DX_VPN_3rd_octet

    except Exception as e:
        return None

def get_SOSV1_AMAZON_INTERFACE(cfg_file,GN):
    try:
        SOSV1_AMAZON_IP = get_SOSV1_EG_IPV4_VARS(cfg_file,GN)[4]
        pattern = r'(family inet address {})'.format(SOSV1_AMAZON_IP)
        get_line = SCRAP_CFG_FILE ( cfg_file=cfg_file, pattern=pattern )
        amazon_inter = re.search ( r'(ge-|xe-|et-)\d{1,2}\/\d{1,2}\/\d{1,2}', get_line[ 0 ] ).group ( 0 )
        return amazon_inter
    except Exception as e:
        logging.error ( "Exception:get_SOSV1_AMAZON_INTERFACE: {}".format ( str ( e ) ) )
        return None

def creating_final_SOS_conf_car(files_dir_car,final_conf_files_names_car,conf_path_car,GN,jb_yaml_path):
    try:
        var_mid_tmp_render = ''
        for x, cfg_file in enumerate ( files_dir_car ):
            for y, final_conf_file in enumerate ( final_conf_files_names_car ):
                if x == y:
                    rendered_config_path = conf_path_car+final_conf_file
                    logging.info ( "Generating VC-CAR CONF File >> {}".format ( final_conf_file ) )
                    SOSV1_EG_IPV6_NEIG = get_SOSV1_EG_IPV6_VARS ( cfg_file,GN )[0]
                    SOSV1_EG_IPV6_CUSTIP = get_SOSV1_EG_IPV6_VARS ( cfg_file,GN )[1]
                    SOSV1_EG_IPV6_PREFIX = get_SOSV1_EG_IPV6_VARS ( cfg_file,GN )[2]
                    SOSV1_EG_NEIG = get_SOSV1_EG_IPV4_VARS ( cfg_file,GN )[0]
                    SOSV1_EG_CUSTIP = get_SOSV1_EG_IPV4_VARS ( cfg_file,GN )[1]
                    SOSV1_EG_PREFIX = get_SOSV1_EG_IPV4_VARS ( cfg_file,GN )[2]
                    SOSV1_EG_VLAN = get_VLAN_for_IPv4 (GN)
                    SOSV1_EG_IPV6_VLAN = get_VLAN_for_IPv6 (GN)
                    SOSV1_CUST_INT = get_SOSV1_CUST_INT ( cfg_file,GN )
                    SOSV1_RID = get_SOSV1_RID ( cfg_file,GN )
                    SOSV1_PEERAS = get_SOSV1_PEERAS (cfg_file,GN)
                    SOSV1_AUTH_KEY = get_SOSV1_AUTH_KEY ( cfg_file,GN )
                    first_deployed_car_KNOB = get_SOSV1_1st_deployed_car ( cfg_file)
                    DX_VPN_LAST_OCTET = str(int(SOSV1_EG_VLAN)+2)
                    DX_VPN_NEIG_LAST_OCTET=str(int(SOSV1_EG_VLAN)+1)
                    SOSV1_DX_VPN_3rd_octet = get_SOSV1_DX_VPN_3rd_OCTET(cfg_file)
                    router_name = final_conf_file[ 0:-5 ]
                    amazon_inter = get_SOSV1_AMAZON_INTERFACE ( cfg_file,GN)
                    SOSV1_EG_CUSTIP_NO_CIDR = SOSV1_EG_CUSTIP[0:-3]
                    JB_YAML = '''- router: {{router_name}}

                      SOSV1-IPv4-V1:
                        Edg Group Metric Name: EdgGroup{{SOSV1_EG_NUM}}
                        Customer Interface Name: {{SOSV1_CUST_INT}}
                        Amazon Interface Name: {{amazon_inter}}
                        Customer IP: {{SOSV1_EG_CUSTIP}}
                        Amazon IP: {{amazon_IP}}/30
                      SOSV1-IPv6-V1:
                        Edg Group Metric Name: Ipv6EdgGroup{{SOSV1_EG_NUM}}
                        Customer Interface Name: {{SOSV1_CUST_INT}}
                        Amazon Interface Name: {{amazon_inter}}
                        Customer IP: {{SOSV1_EG_IPV6_CUSTIP}}
                        Amazon IP: {{SOSV1_EG_IPV6_NEIG}}/125

                    '''
                    JB_tm_yaml = Template ( JB_YAML )
                    JB_YAML_rendered_config = JB_tm_yaml.render ( router_name=router_name, SOSV1_EG_NUM=GN,
                                                                  SOSV1_CUST_INT=SOSV1_CUST_INT,
                                                                  amazon_inter=amazon_inter,
                                                                  SOSV1_EG_CUSTIP=SOSV1_EG_CUSTIP,
                                                                  amazon_IP=SOSV1_EG_NEIG \
                                                                  , SOSV1_EG_IPV6_CUSTIP=SOSV1_EG_IPV6_CUSTIP,
                                                                  SOSV1_EG_IPV6_NEIG=SOSV1_EG_IPV6_NEIG )
                    jb_yaml_file = open ( jb_yaml_path, 'a' )
                    print ( JB_YAML_rendered_config, file=jb_yaml_file )
                    jb_yaml_file.close ()
                    SOS_TEMP = '''policy-options {
    replace: policy-statement TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT {
        term DEFAULT {
            from {
                route-filter {{SOSV1_EG_IPV6_PREFIX}} exact;
                route-filter fdff:ffff:ffff:ffff:ffff:ffff:ffff:{{SOSV1_EG_NUM}}/128 exact;
            }
            then accept;
        }
        term REJECT {
            then reject;
        }
    }

    replace: policy-statement TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT {
        term DEFAULT {
            from {
                route-filter {{SOSV1_EG_PREFIX}} exact;
                route-filter 10.255.255.{{SOSV1_EG_NUM}}/32 exact;
            }
            then accept;
        }
        term REJECT {
            then reject;
         }
    }
{% if first_deployed_car_KNOB == True %}
    replace: policy-statement TESTLOOP-1-DX-VPN-DATA-PLANE-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT {
        term DEFAULT {
            from {
               route-filter {{SOSV1_DX_VPN_3rd_octet}}{{SOSV1_EG_VLAN}}/30 exact;
            }
            then accept;
        }
        term REJECT {
            then reject;
        }
    }
{%- endif %}
}
interfaces {
    {{SOSV1_CUST_INT}} {
        unit {{SOSV1_EG_VLAN}} {
            vlan-id {{SOSV1_EG_VLAN}};
            family inet {
                mtu 1500;
                filter {
                    input TESTLOOP-FILTER;
                }
                address {{SOSV1_EG_CUSTIP}};
            }
        }
        unit {{SOSV1_EG_IPV6_VLAN}} {
            vlan-id {{SOSV1_EG_IPV6_VLAN}};
            family inet6 {
                mtu 1500;
                filter {
                    input TESTLOOP-FILTER-IPV6;
                }
                address {{SOSV1_EG_IPV6_CUSTIP}};
            }
        }
{% if first_deployed_car_KNOB == True %}
        unit 2{{SOSV1_EG_VLAN}} {
             vlan-id 2{{SOSV1_EG_VLAN}};
             family inet {
                 mtu 1500;
                 filter {
                     input TESTLOOP-FILTER;
                 }
                 address {{SOSV1_DX_VPN_3rd_octet}}{{DX_VPN_LAST_OCTET}}/30;
             }
         }
{%- endif %}   
    }
}

routing-instances {
    replace: TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}} {
        instance-type virtual-router;
        interface {{SOSV1_CUST_INT}}.{{SOSV1_EG_VLAN}};
        routing-options {
            static {
                route 10.255.255.{{SOSV1_EG_NUM}}/32 reject;
            }
            multipath;
            autonomous-system 64585;
        }
        protocols {
            bgp {
                group ebgp {
                    neighbor {{SOSV1_EG_NEIG}} {
                        /* com.amazon.awsdx.prod.{{REGION}}.sostenuto.bgp.authkey serial None */
                        authentication-key {{SOSV1_AUTH_KEY}};
                        export TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT;
                        peer-as {{SOSV1_PEERAS}};
                        local-as 64585;
                        bfd-liveness-detection {
                            minimum-interval 300;
                            multiplier 3;
                        }
                        multipath multiple-as;
                    }
                }
            }
        }
    }
    replace: TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-{{SOSV1_EG_NUM}} {
        instance-type virtual-router;
        interface {{SOSV1_CUST_INT}}.{{SOSV1_EG_IPV6_VLAN}};
        routing-options {
            router-id {{SOSV1_RID}}
            multipath;
            autonomous-system 64585;
            rib TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-{{SOSV1_EG_NUM}}.inet6.0 {
                static {
                    route fdff:ffff:ffff:ffff:ffff:ffff:ffff:{{SOSV1_EG_NUM}}/128 reject;
                }
            }
        }
        protocols {
            bgp {
                group ebgp {
                    neighbor {{SOSV1_EG_IPV6_NEIG}} {
                        /* com.amazon.awsdx.prod.{{REGION}}.sostenuto.bgp.authkey serial None */
                        authentication-key {{SOSV1_AUTH_KEY}};
                        export TESTLOOP-1-PRIVATE-IPV6-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT;
                        peer-as {{SOSV1_PEERAS}};
                        local-as 64585;
                        bfd-liveness-detection {
                            minimum-interval 300;
                            multiplier 3;
                        }
                        multipath multiple-as;
                    }
                }
            }
        }
    }
{% if first_deployed_car_KNOB == True %}
    replace: TESTLOOP-1-DX-VPN-DATA-PLANE-EDGGROUP-{{SOSV1_EG_NUM}} {
        instance-type virtual-router;
        interface {{SOSV1_CUST_INT}}.2{{SOSV1_EG_VLAN}};
        routing-options {
            multipath;
            autonomous-system 64585;
        }   
        protocols {
            bgp {
                group ebgp {
                    neighbor {{SOSV1_DX_VPN_3rd_octet}}{{DX_VPN_NEIG_LAST_OCTET}} {
                        authentication-key "$9$12lEclLxNbYg-d5QFnCA8Xx-s2oaUji.X7UjHkPfFn/CA0SreMWxcSrvW87NfTQ3nCtpBcre"; ## SECRET-DATA
                        export TESTLOOP-1-DX-VPN-DATA-PLANE-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT;
                        peer-as {{SOSV1_PEERAS}};
                        local-as 64585;
                        bfd-liveness-detection {
                            minimum-interval 300;
                            multiplier 3;
                       }
                        multipath multiple-as;
                    }
                }
            }
        }
    }
{%- endif %}
}'''
                    tm = Template ( SOS_TEMP )
                    conf_file = tm.render ( SOSV1_EG_NUM=args.GN, SOSV1_RID=SOSV1_RID, SOSV1_CUST_INT=SOSV1_CUST_INT,
                                            SOSV1_EG_VLAN=SOSV1_EG_VLAN, SOSV1_EG_PREFIX=SOSV1_EG_PREFIX,
                                            SOSV1_EG_NEIG=SOSV1_EG_NEIG, SOSV1_EG_CUSTIP=SOSV1_EG_CUSTIP, \
                                            SOSV1_EG_IPV6_VLAN=SOSV1_EG_IPV6_VLAN,
                                            SOSV1_EG_IPV6_PREFIX=SOSV1_EG_IPV6_PREFIX,
                                            SOSV1_EG_IPV6_CUSTIP=SOSV1_EG_IPV6_CUSTIP,
                                            SOSV1_EG_IPV6_NEIG=SOSV1_EG_IPV6_NEIG, REGION=args.region,SOSV1_PEERAS =SOSV1_PEERAS,\
                                            SOSV1_AUTH_KEY=SOSV1_AUTH_KEY,first_deployed_car_KNOB=first_deployed_car_KNOB,
                                            DX_VPN_NEIG_LAST_OCTET=DX_VPN_NEIG_LAST_OCTET,DX_VPN_LAST_OCTET=DX_VPN_LAST_OCTET,SOSV1_DX_VPN_3rd_octet=SOSV1_DX_VPN_3rd_octet)
                    rendered_config = open ( rendered_config_path, 'w+' )
                    print ( conf_file, file=rendered_config )
                    rendered_config.close ()
                    var_mid = '''
                    {'name': "{{router_name}}",
                    'routingInstance': 'TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}}',
                    'sostenutoCustomerIp': '{{SOSV1_EG_CUSTIP_NO_CIDR}}',
                    'sostenutoCustomerPort': '{{SOSV1_CUST_INT}}.{{SOSV1_EG_VLAN}}'},'''
                    var_mid_tmp = Template ( var_mid )
                    var_mid_tmp_render += var_mid_tmp.render ( router_name=router_name, SOSV1_EG_NUM=GN,
                                                               SOSV1_EG_CUSTIP_NO_CIDR=SOSV1_EG_CUSTIP_NO_CIDR, \
                                                               SOSV1_CUST_INT=SOSV1_CUST_INT,
                                                               SOSV1_EG_VLAN=SOSV1_EG_VLAN )
    except Exception as e:
        logging.error ( "Exception: creating_final_SOS_conf_car: {}".format ( str ( e ) ) )
        return None

def creating_final_SOS_conf_cir(files_dir_cir,final_conf_files_names_cir,conf_path_cir,GN):
    try:
        for x, cfg_file in enumerate ( files_dir_cir ):
            for y, final_conf_file in enumerate ( final_conf_files_names_cir ):
                if x == y:
                    rendered_config_path = conf_path_cir+final_conf_file
                    logging.info ( "Generating VC-CIR CONF File >> {}".format ( final_conf_file ) )
                    SOSV1_EG_NEIG = get_SOSV1_EG_IPV4_VARS ( cfg_file,GN )[0]
                    SOSV1_EG_CUSTIP = get_SOSV1_EG_IPV4_VARS ( cfg_file,GN )[1]
                    SOSV1_EG_PREFIX = get_SOSV1_EG_IPV4_VARS ( cfg_file,GN )[2]
                    SOSV1_EG_VLAN = get_VLAN_for_IPv4 (GN)
                    SOSV1_PEERAS_CIR = get_SOSV1_PEERAS_CIR (cfg_file,GN)
                    SOSV1_AUTH_KEY = get_SOSV1_AUTH_KEY ( cfg_file,GN )
                    SOS_TEMP_CIR = '''policy-options {
    replace: policy-statement TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT {
        term DEFAULT {
            from {
                route-filter {{SOSV1_EG_PREFIX}} exact;
                route-filter 10.255.255.{{SOSV1_EG_NUM}}/32 exact;
            }
            then accept;
        }
        term REJECT {
            then reject;
        }
    }
}
interfaces {
    ae102 {
        unit 16{{SOSV1_EG_VLAN}} {
            vlan-tags outer 0x8100.195 inner 0x8100.{{SOSV1_EG_VLAN}};
            family inet {
                mtu 1500;
                filter {
                    input TESTLOOP-FILTER;
                }
                address {{SOSV1_EG_CUSTIP}};
            }
        }
    }
}
routing-instances {
    replace: TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}} {
        instance-type virtual-router;
        interface ae102.16{{SOSV1_EG_VLAN}};
        routing-options {
            static {
                route 10.255.255.{{SOSV1_EG_NUM}}/32 reject;
            }
            multipath;
            autonomous-system 64585;
        }
        protocols {
            bgp {
                group ebgp {
                    neighbor {{SOSV1_EG_NEIG}} {
                        /* com.amazon.awsdx.prod.{{REGION}}.sostenuto.bgp.authkey serial None */
                        authentication-key {{SOSV1_AUTH_KEY}};
                        export TESTLOOP-1-PRIVATE-EDGGROUP-{{SOSV1_EG_NUM}}-ADVERTISEMENT;
                        peer-as {{SOSV1_PEERAS}};
                        local-as 64585;
                        bfd-liveness-detection {
                            minimum-interval 300;
                            multiplier 3;
                        }
                        multipath multiple-as;
                    }
                }
            }
        }
    }
}'''
                    tm = Template ( SOS_TEMP_CIR )
                    conf_file = tm.render ( SOSV1_EG_NUM=args.GN, SOSV1_EG_VLAN=SOSV1_EG_VLAN, SOSV1_EG_PREFIX=SOSV1_EG_PREFIX,SOSV1_EG_NEIG=SOSV1_EG_NEIG, SOSV1_EG_CUSTIP=SOSV1_EG_CUSTIP, \
                                            REGION=args.region,SOSV1_PEERAS =SOSV1_PEERAS_CIR,SOSV1_AUTH_KEY=SOSV1_AUTH_KEY )
                    rendered_config = open ( rendered_config_path, 'w+' )
                    print ( conf_file, file=rendered_config )
                    rendered_config.close ()

    except Exception as e:
        logging.error ( "Exception: creating_final_SOS_conf_cir :{}".format ( str ( e ) ) )
        return None

def git_clone(package, path= "/home/" + os.getlogin() + "/"):
    full_path =  path + package
    full_url = 'ssh://git.amazon.com/pkg/' + package
    try:
        repo = git.Repo.clone_from(full_url ,to_path = f'{full_path}')
        return repo
    except:
        logging.error('Could not clone {}. Exception {}'.format(package, sys.exc_info()))
        return None

def sos_daryl_repo_folder_creation():
    username = os.getlogin ()
    if os.path.exists ( f'/home/{username}/DxVpnCM2014/' ) == True:
        repo = git.Repo ( f'/home/{username}/DxVpnCM2014' )
        origin = repo.remote ( 'origin' )
        logging.info ( 'DxVpnCM2014 repo exists' )
        if os.path.exists ( f'/home/{username}/DxVpnCM2014/cm/{username}' ) == True:
            logging.info ( '{} exists under DxVpnCM2014/cm directory'.format ( username ) )
            logging.info ( 'Performing git pull' )
            origin.pull ()
        else:
            logging.info ( '{} does not exists under DxVpnCM2014/cm directory'.format ( username ) )
            os.mkdir ( f'/home/{username}/DxVpnCM2014/cm/{username}' )
            logging.info ( 'User {} successfully created user directory under DxVpnCM2014/cm'.format ( username ) )
            logging.info ( 'Performing git pull' )
            origin.pull ()
    else:
        logging.info ( 'DxVpnCM2014 repo does not exist' )
        logging.info ( 'Performing git clone on DxVpnCM2014' )
        cloned = git_clone ( 'DxVpnCM2014' )

        if cloned:
            logging.info ( 'git clone successful for DxVpnCM2014' )
            repo = git.Repo ( f'/home/{username}/DxVpnCM2014' )
            origin = repo.remote ( 'origin' )
            if os.path.exists ( f'/home/{username}/DxVpnCM2014/cm/{username}' ) == True:
                logging.info ( '{} exists under DxVpnCM2014/cm directory'.format ( username ) )
                logging.info ( 'Performing git pull' )
                origin.pull ()
            else:
                logging.info ( '{} does not exists under DxVpnCM2014/cm directory'.format ( username ) )
                os.mkdir ( f'/home/{username}/DxVpnCM2014/cm/{username}' )
                logging.info ( 'User {} successfully created user directory under DxVpnCM2014/cm'.format ( username ) )
                logging.info ( 'Performing git pull' )
                origin.pull ()
        else:
            logging.error ( 'git clone failed for DxVpnCM2014. Clone DxVpnCM2014 manually and re-run the script' )
            sys.exit ()

def diff_config(device,directory,password):
    try:
        logging.info ( 'Getting diffs for {}'.format ( device ) )
        completed_process = subprocess.run ('jdop -p {} -d {}{}.diff diff {} {}{}.conf'.format(password,directory,device,device,directory,device),shell=True,stdout=subprocess.PIPE)
        output = completed_process.stdout
        return output
    except Exception as e:
        logging.error ( "Exception:diff_config :{}".format ( str ( e ) ) )
        return None

def get_diffs_for_cars(directory,password):
    for i in vc_car_devices:
        diff_config (i,directory,password )

def get_diffs_for_cirs(directory,password):
    for i in vc_cir_devices:
        diff_config (i,directory,password )

def SOS_MCM_CARS_CREATION(GN,region,max_per_MCM):
    cars_per_MCM = [ ]
    counter=0
    SOSV1_EG_VLAN = get_VLAN_for_IPv4 ( GN )
    SOSV1_EG_IPV6_VLAN = get_VLAN_for_IPv6 ( GN )
    if len ( vc_car_devices ) > max_per_MCM:
        init = 0
        end = max_per_MCM
        for i in range ( math.ceil ( len ( vc_car_devices ) / max_per_MCM ) ):
            cars_per_MCM.append ( vc_car_devices[ init:end ] )
            init = init + max_per_MCM
            end = end + max_per_MCM
    else:
        cars_per_MCM.append ( vc_car_devices )

    for i in cars_per_MCM:
        vc_devices = i
        hostnames = "\n".join ( i )
        counter = counter  + 1
        username = os.getlogin ()
        mcm_info = mcm.mcm_creation ( "sostenuto_for_new_EG_CARS",region,GN,vc_devices,hostnames,SOSV1_EG_VLAN,SOSV1_EG_IPV6_VLAN,counter )
        mcm_id = mcm_info[ 0 ]
        mcm_uid = mcm_info[ 1 ]
        mcm_overview = mcm_info[ 2 ]
        logging.info ( 'https://mcm.amazon.com/cms/{} created'.format ( mcm_id ) )
        mcm_overview_append = f"""
###Lock MCM

```
/apollo/env/Daryl/bin/darylscriptc --lock --cm {mcm_id}
 ```

###Dry-run

```
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode dryrun --no-auto-dashboard --no-hds --no-console
 ```

###Execute MCM

```
1. "inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/)
2. Start Monitoring "Darylmon all" and #netsupport Chime Room. This is to see any ongoing/newly coming Sev2s in AWS Networking
```

```
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode execute
```

###Variable File

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/conf-car-{args.region}-group{args.GN}/{mcm_id}.var

###Configuration and Diff Files

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/conf-car-{args.region}-group{args.GN}/

    """
        # update MCM overview and steps
        mcm_overview_final = mcm_overview + mcm_overview_append
        mcm_steps = [ {'title': 'Daryl Info', 'time': 300,
                       'description': f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/conf-car-{args.region}-group{args.GN}/{mcm_id}.var'} ]
        mcm.mcm_update ( mcm_id, mcm_uid, mcm_overview_final, mcm_steps )
        logging.info (
            '{} successfully updated, please lock the MCM through Daryl and submit for approvals\n'.format ( mcm_id ) )


def SOS_MCM_CIRS_CREATION(GN,region):
    all_az_devices = [ i for i in vc_cir_devices if not re.match ( '.*-vc-(car|rrr).*', i ) ]
    all_az = sorted(set(i.split('-')[0] for i in vc_cir_devices))
    all_az = sorted ( set ( i.split ( '-' )[ 0 ] for i in all_az_devices ) )
    SOSV1_EG_VLAN = get_VLAN_for_IPv4 ( GN )
    cirs_list=list()
    for i in all_az:
        az_devices_list = list ()
        for j in all_az_devices:
            if i == j.split ( '-' )[ 0 ]:
                az_devices_list.append ( j )
        cirs_list.append(az_devices_list)
    for i in cirs_list:
        hostnames = "\n".join ( i )
        username = os.getlogin ()
        cir_devices = i
        AZ = cir_devices[0].split('-')[0].upper()
        mcm_info = mcm.mcm_creation ( "sostenuto_for_new_EG_CIRS",region,GN,cir_devices,hostnames,SOSV1_EG_VLAN,AZ )
        mcm_id = mcm_info[ 0 ]
        mcm_uid = mcm_info[ 1 ]
        mcm_overview = mcm_info[ 2 ]
        logging.info ( 'https://mcm.amazon.com/cms/{} created'.format ( mcm_id ) )
        mcm_overview_append = f"""
###Lock MCM

```
/apollo/env/Daryl/bin/darylscriptc --lock --cm {mcm_id}
 ```

###Dry-run

```
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode dryrun --no-auto-dashboard --no-hds --no-console
 ```

###Execute MCM

```
1. "inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/)
2. Start Monitoring "Darylmon all" and #netsupport Chime Room. This is to see any ongoing/newly coming Sev2s in AWS Networking
```

```
/apollo/env/Daryl/bin/daryl.pl --cm {mcm_id} --mode execute
```

###Variable File

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/conf-cir-{args.region}-group{args.GN}/{mcm_id}.var

###Configuration and Diff Files

https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/{username}/conf-cir-{args.region}-group{args.GN}/

    """
        # update MCM overview and steps
        mcm_overview_final = mcm_overview + mcm_overview_append
        mcm_steps = [ {'title': 'Daryl Info', 'time': 300,
                       'description': f'Daryl URL: brazil://DxVpnCM2014/cm/{username}/conf-cir-{args.region}-group{args.GN}/{mcm_id}.var'} ]
        mcm.mcm_update ( mcm_id, mcm_uid, mcm_overview_final, mcm_steps )
        logging.info (
            '{} successfully updated, please lock the MCM through Daryl and submit for approvals\n'.format ( mcm_id ) )


def main():
    now_time = datetime.datetime.now ()
    setup_logging ()
    global args
    global home
    global vc_car_devices
    global vc_cir_devices
    args = parse_args ()
    validate_input ( args )
    home = str ( Path.home () )
    username = os.getlogin ()
    password = getpass.getpass ( prompt="Please Enter Domain Password (needed for JDOP): " )
    if args.max_per_MCM > 4:
        max_per_MCM = 4
    else:
        max_per_MCM = args.max_per_MCM
    print(
        bcolors.WARNING
        + 'Checking DxVpnCM2014 Repo'
        + bcolors.ENDC
    )
    sos_daryl_repo_folder_creation()
    print(
        bcolors.WARNING
        + 'Conf/DIFF files will be saved in DxVpnCM2014 Repo and Pushed Directly'
        + bcolors.ENDC
    )
    #jdop_logfile = home+'/jdoplogfile-{}.txt'.format ( args.region )
    jb_yaml_path = home+'/SOSV1_{}_EG_{}_JB_parameters.yaml'.format ( args.region,args.GN )
    cfg_path_car = home+"/cfg-car-{}-group{}/".format ( args.region,args.GN )
    if not os.path.exists ( cfg_path_car ):
        os.makedirs ( cfg_path_car )

    cfg_path_cir = home+"/cfg-cir-{}-group{}/".format ( args.region,args.GN )
    if not os.path.exists ( cfg_path_cir ):
        os.makedirs ( cfg_path_cir )

    vc_car_devices = [ ]
    vc_cir_devices = [ ]
    logging.info ('Fetching in-service VC-CARS and VC-CIRS from JB ( Excluding PHX && Centennial CARS/CAS')
    vc_car_devices, vc_cir_devices = sostenuto_devices_to_configure ( args.region )
    for car in vc_car_devices:
        logging.info ( "Generating Full CFG file for {}".format ( car ) )
        cfg_file = cfg_path_car+car+".cfg"
        create_config ( car,cfg_file )
    for cir in vc_cir_devices:
        logging.info ( "Generating Full CFG file for {}".format ( cir ) )
        cfg_file = cfg_path_cir+cir+".cfg"
        create_config ( cir,cfg_file)

    files = [ ]
    for (dirpath, dirnames, filenames) in os.walk ( cfg_path_car ):
        files.extend ( filenames )
        break

    files_cir = [ ]
    for (dirpath, dirnames, filenames) in os.walk ( cfg_path_cir ):
        files_cir.extend ( filenames )
        break

    files_dir_car = [ ]
    for i in files:
        i = cfg_path_car+i
        files_dir_car.append ( i )

    files_dir_cir = [ ]
    for i in files_cir:
        i = cfg_path_cir+i
        files_dir_cir.append ( i )

    conf_path_car = home+"/DxVpnCM2014/cm/{}/conf-car-{}-group{}/".format ( username,args.region,args.GN )
    if not os.path.exists ( conf_path_car ):
        os.makedirs ( conf_path_car )

    final_conf_files_names_car = [ ]
    for i in files:
        i = i.replace ( "cfg", "conf" )
        final_conf_files_names_car.append ( i )

    conf_path_cir = home+"/DxVpnCM2014/cm/{}/conf-cir-{}-group{}/".format ( username,args.region,args.GN )
    if not os.path.exists ( conf_path_cir ):
        os.makedirs ( conf_path_cir )

    final_conf_files_names_cir = [ ]
    for i in files_cir:
        i = i.replace ( "cfg", "conf" )
        final_conf_files_names_cir.append ( i )
    print (bcolors.HEADER,'Generating VC-CARS CONF Files',bcolors.ENDC)
    creating_final_SOS_conf_car(files_dir_car=files_dir_car,final_conf_files_names_car=final_conf_files_names_car,conf_path_car=conf_path_car,GN=args.GN,jb_yaml_path=jb_yaml_path)
    print(
        bcolors.WARNING
        + 'All VC-CAR CONF files saved in {}'.format(conf_path_car)
        + bcolors.ENDC
    )
    print (bcolors.HEADER,'Generating VC-CARS DIFF Files'.format(conf_path_car),bcolors.ENDC)
    get_diffs_for_cars(conf_path_car,password)
    print(
        bcolors.WARNING
        + 'All VC-CAR DIFF files saved in {}'.format(conf_path_car)
        + bcolors.ENDC
    )
    print (bcolors.HEADER,'Generating VC-CIRS CONF Files',bcolors.ENDC)
    creating_final_SOS_conf_cir(files_dir_cir=files_dir_cir,final_conf_files_names_cir=final_conf_files_names_cir,conf_path_cir=conf_path_cir,GN=args.GN)
    print(
        bcolors.WARNING
        + "All VC-CIR CONF files saved in {}".format(conf_path_cir)
        + bcolors.ENDC
    )
    print (bcolors.HEADER,'Generating VC-CIRS DIFF Files',bcolors.ENDC)
    get_diffs_for_cirs(conf_path_cir,password)
    print(
        bcolors.WARNING
        + 'All VC-CIR DIFF files saved in {}'.format(conf_path_cir)
        + bcolors.ENDC
    )
    print(
        bcolors.BOLD
        + 'Creating MCMs For VC-CARS'
       + bcolors.ENDC
    )
    SOS_MCM_CARS_CREATION ( GN=args.GN, region=args.region, max_per_MCM=args.max_per_MCM )
    print(
        bcolors.BOLD
        + 'Creating MCMs For VC-CIRS'
       + bcolors.ENDC
    )
    SOS_MCM_CIRS_CREATION ( GN=args.GN, region=args.region )
    logging.info('Prepping for CONF && DIFF file to be pushed to DxVpnCM2014 repo')
    repo = git.Repo(f'/home/{username}/DxVpnCM2014')
    logging.info('git add')
    repo.index.add([f'/home/{username}/DxVpnCM2014/cm/{username}/conf-car-{args.region}-group{args.GN}/'])
    repo.index.add([f'/home/{username}/DxVpnCM2014/cm/{username}/conf-cir-{args.region}-group{args.GN}/'])
    logging.info('git commit')
    repo.index.commit(f'SOS Files for EG{args.GN} in Region >> {args.region}')
    origin = repo.remote('origin')
    logging.info('git push')
    origin.push()
    logging.info(f'SOS files are successfully pushed to DxVpnCM2014 repo in the following directories /home/{username}/DxVpnCM2014/cm/{username}/conf-car-{args.region}-group{args.GN}/  && /home/{username}/DxVpnCM2014/cm/{username}/conf-cir-{args.region}-group{args.GN}/')
    print (
    bcolors.BOLD
    + 'All JB parameters saved in {} >>> working on automating adding Sostenuto to JB with SW'.format ( jb_yaml_path )
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

