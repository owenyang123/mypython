#!/apollo/sbin/envroot "$ENVROOT/bin/python"
from dxd_tools_dev.modules import (mcm,mobius,jukebox,nsm)
import pandas as pd
import xlwt
import xlrd
import subprocess
import argparse
import string
import sys
import re
import os
import requests
import xlrd
import uuid
from time import perf_counter

'''
Script to create Mobius topologies and run jobs

usage: dx_mobius.py [-h] [-m] [-a] [-z] [-t] [-cr] [-d] [-cp] [-cl] [-pt]
                    [-lt]

Script for Mobius topology and job creation

optional arguments:
  -h, --help            show this help message and exit
  -m , --cutsheet_mcm   CSV FILE FOR MOBIUS WITH LINK INFO (ex:"test.csv"
  -a , --a_side_regex   A SIDE REGEX (EX: "vc-bar"
  -z , --z_side_regex   Z SIDE REGEX (EX: "vc-bar"
  -t , --topology_id    TOPOLOGY ID (EX: "1234")
  -cr, --create_topology
                        CREATE TOPOLOGY UNDER MOBIUS
  -d, --delete_topology
                        DELETE TOPOLOGY UNDER MOBIUS
  -cp, --create_topology_link_test
                        CREATE TOPOLOGY AND RUN LINK TEST
  -cl, --create_topology_lldp_test
                        CREATE TOPOLOGY AND RUN LLDP TEST
  -pt, --create_link_test
                        CREATE LINK TEST FOR A GIVEN TOPOLOGY
  -lt, --create_lldp_test
                        CREATE LLDP TEST FOR A GIVEN TOPOLOGY

examples
create topology
brazil-runtime-exec python3 dx_mobius.py --cutsheet_mcm 'MCM-34028330' --a_side_regex 'vc-bar' --z_side_regex 'vc-edg' --create_topology

delete topology
brazil-runtime-exec python3 dx_mobius.py --cutsheet_mcm 'MCM-34028330' --topology_id '1234' --delete_topology

create topology and run Read Only link test
brazil-runtime-exec python3 dx_mobius.py --cutsheet_mcm 'MCM-34028330' --a_side_regex 'vc-bar' --z_side_regex 'vc-edg' --create_topology_link_test

create topology and run Read LLDP test
brazil-runtime-exec python3 dx_mobius.py --cutsheet_mcm 'MCM-34028330' --a_side_regex 'vc-bar' --z_side_regex 'vc-edg' --create_topology_lldp_test

Author  :   anudeept@
Version :   1.3
'''

class bcolors:
	CLEARBLUE = '\033[96m'
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	WARNING = '\033[93m'
	OKGREEN = '\033[92m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Script for Mobius topology and job creation")
    parser.add_argument('-m','--cutsheet_mcm', type=str, metavar = '', required= False, help = 'CSV FILE FOR MOBIUS WITH LINK INFO (ex:"test.csv"')
    parser.add_argument('-r','--region', type=str, metavar = '', required= False, help = 'REGION EX: IAD')
    parser.add_argument('-a','--a_side_regex',type = str,metavar='', required = False, help = 'A SIDE REGEX (EX: "vc-bar"')
    parser.add_argument('-z','--z_side_regex',type = str,metavar='', required = False, help = 'Z SIDE REGEX (EX: "vc-bar"')
    parser.add_argument('-t','--topology_id',type = str,metavar='', required = False, help = 'TOPOLOGY ID (EX: "1234")')
    parser.add_argument("-cr","--create_topology",action="store_true",help="CREATE TOPOLOGY UNDER MOBIUS")
    parser.add_argument("-d","--delete_topology",action="store_true",help="DELETE TOPOLOGY UNDER MOBIUS")
    parser.add_argument("-cp","--create_topology_link_test",action="store_true",help="CREATE TOPOLOGY AND RUN LINK TEST")
    parser.add_argument("-cl","--create_topology_lldp_test",action="store_true",help="CREATE TOPOLOGY AND RUN LLDP TEST")
    parser.add_argument("-pt","--create_link_test",action="store_true",help="CREATE LINK TEST FOR A GIVEN TOPOLOGY")
    parser.add_argument("-lt","--create_lldp_test",action="store_true",help="CREATE LLDP TEST FOR A GIVEN TOPOLOGY")
    return parser.parse_args()

def cutsheet_to_csv(cutsheet_mcm : str,a_regex : str,z_regex : str,region):
    """This function reads cutsheet converts to CSV and returns device links which are needed to create 
    Mobius topology

    ex: content = cutsheet_to_csv('MCM-1234',['iad6-vc-bar-r1','iad6-vc-bar-r2'])

    Args:
        cutsheet_mcm (str): Cutsheet MCM, ex: '1234'
        device_list (list): List of devices

    Returns:
        content (str): String of device links
        ex: 'iad61-vc-bar-r101,xe-0/0/0:0,iad61-br-agg-r1,xe-10/0/0\niad61-vc-bar-r101,xe-0/0/0:1,iad61-br-agg-r1,xe-10/0/2\niad61-vc-bar-r101,xe-0/0/0:2,iad61-br-agg-r1,xe-10/0/3\n'
    """
    #download cutsheet from mcm.py module
    print("[Info] : Downloading cutsheet from the MCM provided")
    try:
        cutsheet = mcm.download_latest_cutsheet(cutsheet_mcm)
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    
    #read cutsheet
    try:
        df = pd.read_excel(cutsheet,engine="xlrd",sheet_name=None)
    except Exception as error:
        print("[Error] : Error reading - {error} ")
        sys.exit()

    df_new = pd.DataFrame()
    if len(df) != 0:
        for info in df.items():
            df_new = df_new.append(info[1])
    else:
        print(bcolors.FAIL,f'Error >> Excel sheet is not in the right format, please verify',bcolors.ENDC)
        sys.exit()

    try:
        df_new = df_new[['a_hostname','a_interface','z_hostname','z_interface']]
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    
    #strip whitespaces in all columns 
    df_new[df_new.columns] = df_new.apply(lambda x: x.str.strip())
    #drop NaN
    df_new = df_new.dropna(axis=0,how='all')
    df_new = df_new.dropna(axis=1,how='all')
    #search for regex in dataframe
    try:
        df_final=df_new[df_new.a_hostname.str.contains(a_regex, regex= True, na=False) & df_new.z_hostname.str.contains(z_regex, regex= True, na=False)]
    except Exception as error:
        print(bcolors.FAIL,f'[Error] : {error}',bcolors.ENDC)
        sys.exit()
    if len(df_final)!=0:
        print(bcolors.OKGREEN,"[Info]: User provided regex is valid",bcolors.ENDC)
    else:
        print(bcolors.FAIL,f'[Error]: Please check the arguments provided for a_side_regex and z_side_regex',bcolors.ENDC)
        sys.exit()
    df_final = df_final[df_final['a_interface'] != 'em0']
    df_final = df_final[df_final['a_interface'] != 'fxp0']
    df_final = df_final[df_final['a_interface'] != 'mgmt']
    df_final = df_final[df_final['a_interface'] != 'mgt']
    df_final = df_final[df_final['z_interface'] != 'em0']
    df_final = df_final[df_final['z_interface'] != 'fxp0']
    df_final = df_final[df_final['z_interface'] != 'mgmt']
    df_final = df_final[df_final['z_interface'] != 'mgt']
    df_final = df_final.drop_duplicates()
    csv_file = df_final.to_csv(index=False)
     #convert rows to list
    output = df_final.values.tolist()
    content = ""
    for line in output:
        content += ','.join(line)+'\n'
    # print("[Info] : Getting region for the list of devices")
    # df_head_1 = df_new.head(1)
    # sample_device = df_head_1.a_hostname.values[0]
    # try:
    #     devie_info = nsm.get_devices_region_from_nsm(sample_device)
    # except Exception as error:
    #     print("[Error] : Could not determine region, exiting")
    # region = devie_info[0]['NSM_Stack']
    return content,region

def mobius_topology_creation(region : str,content : str):
    """Function to create Mobius topology, takes content from cutsheet_to_csv function

    Args:
        region (str): Region for devices ex:'iad'
        content (str): Link info 
    """
    #create random toplogy name 
    id = uuid.uuid1()
    topology_name  = os.getlogin()+'_'+ str(id)
    #instantiate Mobius class
    mobius_topology = mobius.Mobius()
    #CreateCutsheetTopology( self,region:str,content:str,topology_name:str )
    topology = mobius_topology.CreateCutsheetTopology( region,content,topology_name )
    return topology

def mobius_topology_deletion(topology_id : str):
    """This function deletes the topology created.To use this function, instantiate the class and call it

    example:
    x = Mobius()
    resp = x.DeleteTopology(1234)

    Args:
        topology_id ([integer]): Topology id, should be integer
    """
    #instantiate Mobius class
    mobius_topology = mobius.Mobius()
    #DeleteTopology(self,topology_id:int)
    topology = mobius_topology.DeleteTopology(topology_id)
    return topology

def create_topology_link_test(region : str,content : str ):
    """This function create Mobius topology and also starts the Read Only Link job

    Args:
        region (str): Region where the mobius topology is created ex: 'iad'
        content (str): Link info from cutsheet

    """
    print(bcolors.OKBLUE,f'[Info] : Creating Mobius Topology')
    #create random toplogy name
    id = uuid.uuid1()
    topology_name  = os.getlogin()+'_'+ str(id)
    #instantiate Mobius class
    mobius_topology = mobius.Mobius()
    #CreateCutsheetTopology( self,region:str,content:str,topology_name:str )
    topology = mobius_topology.CreateCutsheetTopology( region,content,topology_name )
    topology_id = topology[0]
    print(bcolors.OKBLUE,f'[Info] : Creating Read Only Link test for topology {topology_id}',bcolors.ENDC)
    # call CreateJobLink( self,topology_id:str,testplan:str) from mobius module
    job_resp = mobius_topology.CreateJobLink(topology_id,'Read Only')
    job_id = job_resp.properties['id']
    print(f'[Info] : Check https://mobiuschecker-pdx.pdx.proxy.amazon.com/topologies/{topology_id}/jobs/{job_id}')
    return job_resp

def create_topology_lldp_test(region : str,content : str ):
    """This function create Mobius topology and also starts the LLDP job

    Args:
        region (str): Region where the mobius topology is created ex: 'iad'
        content (str): Link info from cutsheet

    """
    print(bcolors.OKBLUE,f'[Info] : Creating Mobius Topology')
    #create random toplogy name
    id = uuid.uuid1()
    topology_name  = os.getlogin()+'_'+ str(id)
    #instantiate Mobius class
    mobius_topology = mobius.Mobius()
    #CreateCutsheetTopology( self,region:str,content:str,topology_name:str )
    topology = mobius_topology.CreateCutsheetTopology( region,content,topology_name )
    topology_id = topology[0]
    print(bcolors.OKBLUE,f'[Info] : Creating Read Only Link test for {topology_id}',bcolors.ENDC)
    # call CreateJobLink( self,topology_id:str,testplan:str) from mobius module
    job_resp = mobius_topology.CreateJobTopology(topology_id,'LLDP')
    job_id = job_resp.properties['id']
    print(f'[Info] : Check https://mobiuschecker-pdx.pdx.proxy.amazon.com/topologies/{topology_id}/jobs/{job_id}')
    return job_resp

def main():
    start_time = perf_counter()
    args = parse_args()
    if args.cutsheet_mcm:
        info = cutsheet_to_csv(args.cutsheet_mcm,args.a_side_regex ,args.z_side_regex,args.region)
        content = info[0]
        region = info[1]
    if args.create_topology:
        try:
            mobius_topology_creation(region,content)
        except Exception as error:
            print(f'[Error] : {error}')
    elif args.delete_topology:
        try:
            mobius_topology_deletion(args.topology_id)
        except Exception as error:
            print(f'[Error] : {error}')
    elif args.create_topology_link_test:
        try:
            create_topology_link_test(region,content)
        except Exception as error:
            print(f'[Error] : {error}')
    elif args.create_topology_lldp_test:
        try:
            create_topology_lldp_test(region,content)
        except Exception as error:
            print(f'[Error] : {error}')
    else:
        print(bcolors.FAIL,f'[Error] : User did not specify the right argument, please run --help for arguments',bcolors.ENDC)
        sys.exit()  
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.BOLD,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)

if __name__ == "__main__":
    main()
