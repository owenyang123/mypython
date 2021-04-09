#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import re
import subprocess
import argparse
import sys
from dxd_tools_dev.modules import nsm
from dxd_tools_dev.portdata import border as portdata
from dxd_tools_dev.modules import jukebox
from com.amazon.jukebox.getdevicedetailsrequest import GetDeviceDetailsRequest

####################################################################################################
#  Summary: This script is to generate var file for BR-AGG pre-stage/Scaling towards DX devices    #
#  Usage:                                                                                          #
#  br_agg_var -r <router> -c <cr number>                                                           #
#  br_agg_var -r "fra53-br-agg-r3" -c 18880221                                                     #
#                                                                                                  #
#  Version: 1.0                                                                                    #
#  Author : aaronya@                                                                               #                                                                          #                   
####################################################################################################

# Var file is for the template of "rbe_standard_dcr_and_agg_tiedown_sitecast.yaml" but variables for Tie down is not automated yet! 


def main():
	parser = argparse.ArgumentParser(description="Script to generate var file for BR-AGG pre-stage/scaling towards DX devices")
	parser.add_argument('-r','--router', type=str, metavar = '', required = True, help = 'please type in the Br-agg device name')
	parser.add_argument('-c','--cr', type=str, metavar = '', required = True, help = 'please type in the CR Number')
	args = parser.parse_args()
	cr_information=get_cr_information(args.cr)
	hostname=args.router
	site_code=get_site_code(hostname)
	var_file = '{}.var'.format(hostname)	

	results=read_cr_information(cr_information,hostname)
	results['LOCAL_COR']=get_local_cor(site_code)
	results['NSM_UPDATED_BY']=get_user_name()
	PEERIP='PEER_IP_ADDRESS_AGG_R'+hostname[-1]
	results[PEERIP]=results['PEER_IP_ADDRESS']
	results.pop('PEER_IP_ADDRESS', None)
	results['NEW_LAGS_EXIST']="false"
	results['NEW_LAGS_NOT_EXIST']="true"


	in_service_state=['OPERATIONAL','MAINTENANCE']
	new_dx_device=[]
	results['VC_LOOPBACK']=[]

	if "MX" in nsm.get_device_hardware_from_nsm(hostname)['Chassis'][0]:
		results['IS_MX_DEVICE']='true'
	else:
		results['IS_MX_DEVICE']='false'


	for device in results['DX_DEVICE']:
		if check_device_status(device) not in in_service_state:
			new_dx_device.append(device)
	
	if len(new_dx_device)>0:
		results['NEW_VC_DEVICE']="true"
		results["NOT_NEW_VC_DEVICE"]="false"
		for router in new_dx_device:
			results['VC_LOOPBACK'].append(get_dx_device_loopback(router)+'/32')
	else:
		results['NEW_VC_DEVICE']="false"
		results["NOT_NEW_VC_DEVICE"]="true"

	for lag in results['AE_TO_VC_DEVICES']:
		if check_lag_exist(lag,hostname) == "true":
			results['NEW_LAGS_EXIST']="true"
			results['NEW_LAGS_NOT_EXIST']="false"
			break
		else:
			pass

	if results['NEW_LAGS_NOT_EXIST']=='false':
		results['DX_PRESTAGE']='true'
	else:
		results['DX_PRESTAGE']='false'


	with open(var_file,'w') as f:
		for key,value in results.items():
			if type(value)==list:
				print('{}={}'.format(key,','.join(value)))
				f.write('{}= {}\n'.format(key, ','.join(value)))
			else:
				print('{}={}'.format(key,value))
				f.write('{}= {}\n'.format(key, value))

	print("\n{}.var file for br-agg generated successfully.".format(hostname))	

def get_cr_information(cr_number):
	cr_infor_raw = subprocess.check_output("cd ~/GenevaBuilder && git log --grep {} | grep commit | awk '{{print $2}}' | xargs -i git diff {{}}^ {{}}".format(cr_number),shell=True)
	cr_infor = str(cr_infor_raw, encoding = 'utf-8')
	if len(cr_infor)==0:
		print("Please confirm CR number and ensure GB is installed in cd ~/GenevaBuilder with the latest information")
		sys.exit()
	else:
		return(cr_infor)

def get_site_code(hostname):
	site_code=[]
	for character in hostname.split('-')[0]:
		if character.isalpha():
			site_code.append(character)
	return(''.join(site_code))

def get_local_cor(site_id):
	cor_regex="name:/{}.*br-cor-r.*/".format(site_id)
	border_core_devices=sorted(nsm.get_devices_from_nsm(cor_regex))
	return(border_core_devices[0])


def get_user_name():
	user_raw = subprocess.check_output("echo $HOME",shell=True)
	user=str(user_raw, encoding = 'utf-8').split('/')[-1].strip()
	return(user)
	

def read_cr_information(cr_information,router):
	results={}
	results['INTERFACES_TO_TURNUP']=[]
	results['AE_TO_VC_DEVICES']=[]
	results['IPV4_P2P']=[]
	results['PEER_IP_ADDRESS']=[]
	results['DX_DEVICE']=[]

	interest_line=False
	for line in cr_information.splitlines():
		if line.startswith("+++ b/targetspec/border/{}".format(router)):
			interest_line=True
		if interest_line and line.startswith("+"):
			pattern = r'\+CUSTOMER VPC IFACE (\S+) MEMBER (\S+) REMPORT (\S+)'
			match = re.search(pattern,line)
			if match:
				if match.group(1) not in results['AE_TO_VC_DEVICES']:
					results['AE_TO_VC_DEVICES'].append(match.group(1))
				if match.group(2) not in results['INTERFACES_TO_TURNUP']:
					results['INTERFACES_TO_TURNUP'].append(match.group(2))
			else:
				pattern = r'\+CUSTOMER VPC IFACE (\S+) VLAN (\S+) IPADDR (\S+)'
				match = re.search(pattern,line)
				if match:
					results['IPV4_P2P'].append(match.group(3))
				else:
					pattern =r'\+CUSTOMER .* NEIGHIP (\S+) LOCALIP (\S+)'
					match = re.search(pattern,line)
					if match:
						results['PEER_IP_ADDRESS'].append(match.group(1))
					else:
						pattern=r'\+CUSTOMER VPC IFACE (\S+) REMDEVICE (\S+)'
						match = re.search(pattern,line)
						if match:
							results['DX_DEVICE'].append(match.group(2))	


		if line.startswith("+++ b/targetspec/border/") and router not in line:
			interest_line = False


	results['DX_DEVICE']=[item.replace('"', '') for item in results['DX_DEVICE']]
	results['INTERFACES_TO_TURNUP_ILS']=results['INTERFACES_TO_TURNUP']+results['AE_TO_VC_DEVICES']
	if len(results['INTERFACES_TO_TURNUP']) !=0:
		results['CHECK_PHYSICAL_INTERFACE_STATE_UP_DOWN']="true"
	else:
		results['CHECK_PHYSICAL_INTERFACE_STATE_UP_DOWN']="false"

	return(results)

def check_device_status(device):
	router=nsm.get_device_detail_from_nsm(device)
	try:
		return(router['Life_Cycle_Status'])
	except TypeError:
		return("Not in NSM")

def get_dx_device_loopback(router):
	endpoint_info = jukebox.get_device_jukebox_region_endpoint(router)
	jukebox_conn = jukebox.jukebox_connector(endpoint_info['aws_region'], endpoint_info['jukebox_endpoint'] , endpoint_info['region'])
	detail = GetDeviceDetailsRequest(router)
	GetDeviceDetailsResult=jukebox_conn.get_device_details(detail)
	return(GetDeviceDetailsResult.data.device.loopback_addresses[0].ipv4_address)


def check_lag_exist(lag, router):
	config = subprocess.check_output('/apollo/env/HerculesConfigDownloader/bin/hercules-config get --hostname {} latest --file set-config'.format(router),shell=True)
	config = str(config, encoding = 'utf-8')
	key_word = 'set interfaces ' + lag
	if key_word in config:
		return "true"
	else:
		return "false"




if __name__ == "__main__":
   main()
