#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from __future__ import print_function

'''
MPLSoUDP Deployment Assistant (MUDA)

Version   Date         Author     Comments
1.00      2019-08-27   joaq@      MUDA Beta (beta version, first automation on VC-COR for IP allocation)
2.00      2020-01-13   joaq@      MUDA Alfa (first published version, does IP allocation and GB attributes in separate functions)
3.00      2020-03-09   joaq@      MUDA Auto (full VC-COR deployment automation on 26 steps, automates IP allocation, 4 CRs and 14 MCMs, no user input)
4.00      2020-05-25   joaq@      MUDA Flex (making functions generic to cover Phoenix/Centennial deployments in 36 steps)
5.00      2020-07-22   joaq@      MUDA covers Phoenix/Centennial/Heimdall/VC-DAR deployments in 43 steps.
6.00      2020-10-09   joaq@      MUDA covers first steps of the ClaymoreHD deployments (IP, port reservations and Jukebox)
6.00      2020-12-11   joaq@      Modularization, created muda_genevabuilder.py, muda_auxiliary.py and muda_data.json
7.00      2020-12-11   ajijolao@  MUDA covers first steps of the Telesto(DX2.0) Deployment (IP, port reservations,Jukebox, BGP Prestage)

MUDA is a DX Deployment automation tool:
https://w.amazon.com/bin/view/DXDEPLOY/Runbooks/MUDA/

'''


muda_progress_legend = """
Deployment Steps:

   << Before MUDA >>
  (00) Port Recycling
  (01) Site Assessment
  (02) Cutsheet MCM
  (03) BOM MCM
  (04) Order RSPV, HW, Cabling
  (05) Linecard replacement/insertion
  (06) BMN port reservation CR/MCM

  << Start MUDA >>
  (07) IP Allocations, BMN IP and DNS + Reserve SOO; IPv6 on VC-COR
  (08) Port Reservation CR
  (09) Port Reservation MCM
  (10) Conditional Manual Tasks
  (11) Create Jukebox Devices, Cabling and Links
  (12) DX side Port Reservation MCM
  (13) Scaling Port testing Mobius
  (14) Scaling Port Shutdown MCM
  (15) ACLManage MCM before prestage
  (16) GenevaBuilder attributes CR
  (17) Border release and prestage from AutoPCN and ManualPCN
  (18) VC-COR console, software and cabling validation
  (19) GenevaBuilder LAG attributes CR
  (20) Brick provisioning
  (21) Brick Mobius testing
  (22) Border/Brick Prestage MCM
  (23) ACLManage MCM after prestage
  (24) SLAX and Herbie prevalidation
  (25) BR-KCT Normalization CR
  (26) BR-KCT Normalization MCM
  (27) VC-COR IXOps Handoff
  (28) Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD console, software and cabling validation
  (29) Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD provisioning
  (30) Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD Mobius testing
  (31) IBGP Mesh MCM
  (32) MMR Port Testing
  (33) Control Plane Turn-up
  (34) Sostenuto Setup
  (35) Data Plane Turn-Up
  (36) LOA Validation and DXDashboard
  (37) IXOps Handoff MCM
  (38) Deployment completed
"""



import os
import socket
import re
import subprocess
import sys
import getpass
import urllib
import json
import calendar
import time
import requests
import signal
import pandas
import prettytable
import datetime
import platform
import logging
from cmd import Cmd
import random
import concurrent.futures
from subprocess import PIPE,STDOUT

from dxd_tools_dev.modules import dogfish, wiki, dns, mcm, cr, nsm, mwinit_cookie, jukebox, region_local, hercules, bundle_service
from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.muda import muda_genevabuilder, muda_auxiliary, muda_dogfish, muda_cutsheet
#from isd_tools_dev.modules import hercules

from com.amazon.dogfish.ipprefix import IPPrefix
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
from netaddr import IPNetwork,cidr_merge
from coral import coralrpc
from http.client import HTTPSConnection
from base64 import b64encode

from com.amazon.jukebox.jukeboxservice import JukeboxServiceClient
from com.amazon.jukebox.getdevicedetailsresult import GetDeviceDetailsResult
from com.amazon.jukebox.getdevicedetailsrequest import GetDeviceDetailsRequest
from com.amazon.jukebox.getdevicesrequest import GetDevicesRequest
from com.amazon.jukebox.getdevicesresult import GetDevicesResult
from pyodinhttp import odin_retrieve, odin_retrieve_pair, OdinOperationError, odin_material_retrieve
from dxd_tools_dev.datastore.ddb import get_device_endpoint_from_site_table as get_device_jukebox_region_endpoint
from dxd_tools_dev.datastore.ddb import get_site_jukebox_region_endpoint
from com.amazon.jukebox.coraldevice import CoralDevice
from com.amazon.jukebox.editdevicerequest import EditDeviceRequest
from com.amazon.jukebox.devicedetails import DeviceDetails
from com.amazon.jukebox.devicecabling import DeviceCabling
from com.amazon.jukebox.devicelink import DeviceLink
from com.amazon.jukebox.adddevicerequest import AddDeviceRequest

from com.amazon.modeledcmapi.modeledcmapiservice import ModeledCmApiServiceClient
from com.amazon.modeledcmapi.requests.cmrequests.getcmrequest import GetCmRequest
from com.amazon.modeledcmapi.requests.cmrequests.createcmrequest import CreateCmRequest
from com.amazon.modeledcmapi.requests.steprequests.createsteprequest import CreateStepRequest
from com.amazon.modeledcmapi.requests.cmrequests.modifycmoverviewrequest import ModifyCmOverviewRequest
from com.amazon.modeledcmapi.datatypes.cmoverview.inputs.cmoverviewtocreate import CmOverviewToCreate
from com.amazon.modeledcmapi.datatypes.cmoverview.inputs.cmoverviewtomodify import CmOverviewToModify
from com.amazon.modeledcmapi.datatypes.steps.inputs.steptocreate import StepToCreate
from com.amazon.modeledcmapi.datatypes.steps.inputs.stepstocreate import StepsToCreate
from com.amazon.modeledcmapi.datatypes.stepchecklists.inputs.stepchecklistitemtocreate import StepChecklistItemToCreate
from com.amazon.modeledcmapi.datatypes.stepchecklists.inputs.stepcheckliststocreate import StepChecklistsToCreate
from com.amazon.modeledcmapi.datatypes.cmowners.cmowner import CmOwner
from com.amazon.modeledcmapi.datatypes.locations.cmlocations import CmLocations
from com.amazon.modeledcmapi.datatypes.cti.cti import Cti
from com.amazon.modeledcmapi.datatypes.locations.availabilityzone import AvailabilityZone
from com.amazon.modeledcmapi.datatypes.locations.awsregion import AwsRegion
from com.amazon.modeledcmapi.datatypes.locations.physicaldatacenter import PhysicalDataCenter
from com.amazon.modeledcmapi.datatypes.approvers.inputs.approvertocreate import ApproverToCreate
from com.amazon.modeledcmapi.datatypes.approvers.inputs.approverstocreate import ApproversToCreate
from com.amazon.modeledcmapi.datatypes.identifiers.assignedapprover import AssignedApprover
from com.amazon.modeledcmapi.datatypes.identifiers.cmfriendlyidentifier import CmFriendlyIdentifier
from com.amazon.modeledcmapi.datatypes.exceptions.recordnotfoundexception import RecordNotFoundException
from com.amazon.modeledcmapi.datatypes.identifiers.targetforauditentry import TargetForAuditEntry
from com.amazon.modeledcmapi.requests.auditentryrequests.getauditentriesrequest import GetAuditEntriesRequest
from com.amazon.coral.availability.throttlingexception import ThrottlingException
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',

if re.search(r"1200.\.dub2",platform.node()):
	logging.getLogger('bender.config.service.ConfigProvider').setLevel(logging.CRITICAL)

border_infra_blocks = [{"scope":"PublicIP","prefix":"150.222.0.0/16"}, {"scope":"PublicIP","prefix":"15.230.0.0/16"}]

class bcolors:
	lightcyan='\033[96m'
	cyan='\033[36m'
	lightblue='\033[94m'
	blue='\033[34m'
	purple='\033[35m'
	black='\033[30m'
	red='\033[31m'
	green='\033[32m'
	orange='\033[33m'
	lightgrey='\033[37m'
	darkgrey='\033[90m'
	lightred='\033[91m'
	lightgreen='\033[92m'
	yellow='\033[93m'
	pink='\033[95m'
	end = '\033[0m'

muda_json = open('/apollo/env/DXDeploymentTools/muda/muda_data.json','r')
muda_data = json.load(muda_json)

#############################################################################################################
##########################################  01. Helper functions  ###########################################
#############################################################################################################

#******************************************#
def get_br_cor_lo(br_cor):
	border_folder = muda_auxiliary.get_border_folder(br_cor)
	command = "cat {}/targetspec/{}/{}/routerspecific.attr | grep PRIMARYIP | grep -v PRIMARYIPV6".format(user["gb_path"],border_folder,br_cor)
	#print(command)
	br_cor_lo = ""
	try:
		output = subprocess.check_output(command, shell=True)
		#ssh network-config-builder-12001.dub2.corp.amazon.com 'cat /home/joaq/GenevaBuilder/targetspec/border/iad2-br-cor-r1/routerspecific.attr | grep PRIMARYIP | grep -v PRIMARYIPV6'
		devices = output.decode()
		br_cor_lo = devices.split()[1]
	except:
		print(bcolors.red,"PRIMARYIP Not found for {}".format(br_cor),bcolors.end)
	return br_cor_lo

#******************************************#
def get_metro_igp():
	bgpmetroigp = ""
	sites = ""
	#this file is shared in border and border-cn folders
	command1 = "cat {}/targetspec/border/global/bgpmetroigp.attr".format(user["gb_path"])
	command2 = "ls {}/targetspec/border | egrep br-cor-r1".format(user["gb_path"])

	try:
		output = subprocess.check_output(command1, shell=True)
		#ssh network-config-builder-12001.dub2.corp.amazon.com 'more targetspec/border/global/bgpmetroigp.attr'
		bgpmetroigp = output.decode()

		output = subprocess.check_output(command2, shell=True)
		#ssh network-config-builder-12001.dub2.corp.amazon.com '/targetspec/border | egrep "*-br-cor-r1"
		sites = output.decode()
	except:
		pass
	return bgpmetroigp,sites

#******************************************#
def search_border_peers(site,device):
	if device == "br-ubq":
		device = "br-ubq-tor"
	pattern = site + "-" + device
	list_devices = []
	border_folder = muda_auxiliary.get_border_folder(site)
	command = "ls {}/targetspec/{} | grep {}".format(user["gb_path"],border_folder,pattern)

	try:
		output = subprocess.check_output(command, shell=True)
		#ssh network-config-builder-12001.dub2.corp.amazon.com 'ls /home/joaq/GenevaBuilder/targetspec/border | grep iad4-br-kct'
		devices = output.decode()
		list_devices = devices.split()
	except:
		pass
	return list_devices

#******************************************#
def check_mcm_completed_successful(last_mcm,modeledcm):
	cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
	uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
	cm_status = uuid.cm.status_and_approvers.cm_status
	if cm_status  == 'Completed':
		cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
		if cm_code == 'Successful':
			print(f"\n   {last_mcm} is Completed Successful, moving to the next step.")
			return True
		else:
			print(f"\n   {last_mcm} is Completed, but {cm_code}.")
	else:
		print(f"\n   {last_mcm} is {cm_status}.")
	return False


#############################################################################################################
##########################################  02. File handlers  ##############################################
#############################################################################################################

#******************************************#
def muda_mkdir():
	if not os.path.exists("{}/MUDA".format(user["muda_path"])):
		try:
			command = "mkdir {}/MUDA".format(user["muda_path"])
			output = subprocess.check_output(command, shell=True)
		except:
			print(bcolors.red,">>   Error creating MUDA directories.",bcolors.end)
	if not os.path.exists("{}/MUDA/Cutsheets".format(user["muda_path"])):
		try:
			command = "mkdir {}/MUDA/Cutsheets".format(user["muda_path"])
			output = subprocess.check_output(command, shell=True)
		except:
			print(bcolors.red,">>   Error creating MUDA directories.",bcolors.end)
	return 0

#******************************************#
def ncb_slink(slink):
	command = "ln -s {}".format(slink)

	try:
		output = subprocess.check_output(command, shell=True)
		#ssh network-config-builder-12001.dub2.corp.amazon.com 'ln -s ../shared/br-kct-border-if-colored.attr /home/joaq/GenevaBuilder/targetspec/border/iad4-vc-cor-b1-r1/br-kct-border-if-colored.attr'
	except:
		pass
	return 0

#******************************************#
def ncb_append(src_path,dst_path):
	command = "cp {} {}_original".format(dst_path,src_path)

	try:
		output = subprocess.check_output(command, shell=True)
		#scp network-config-builder-12001.dub2.corp.amazon.com:/home/joaq/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr /home/joaq/MUDA/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr_original
		my_file = "{}".format(src_path)
		gb_file = "{}_original".format(src_path)
		file = open(my_file, "r")
		data = file.read()
		file.close()
		file = open(gb_file, "a")
		file.write(data)
		file.close()
		command = "cp {}_original {}".format(src_path,dst_path)
		output = subprocess.check_output(command, shell=True)
		#scp /home/joaq/MUDA/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr_original network-config-builder-12001.dub2.corp.amazon.com:/home/joaq/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr
	except:# If the file doesn't exist, we upload the new one.
		command = "cp {} {}".format(src_path,dst_path)
		output = subprocess.check_output(command, shell=True)
		#scp /home/joaq/MUDA/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr network-config-builder-12001.dub2.corp.amazon.com:/home/joaq/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr
	return 0


#############################################################################################################
##########################################  07. GenevaBuilder and ACLManage functions  ######################
#############################################################################################################

#******************************************#
def geneva_builder_append(created_files):
	gb_groups = []
	for k in created_files:
		if created_files[k]["type"] == "GB append":
			gb_groups.append(k)

	for k in gb_groups:
		print("\n>> Appending GB attr for {}:".format(k))
		border_folder = muda_auxiliary.get_border_folder(k)
		for file in created_files[k]["files"]:
			src_path = file
			dst_path = user["gb_path"] + "/targetspec/"+ border_folder+ "/" + file.split('/')[-2] + "/" + file.split('/')[-1]
			#src_path = "/home/joaq/MUDA/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr"
			#dst_path = "/home/joaq/GenevaBuilder/targetspec/border/iad4-br-kct-p1-r1/kct-lagmembers.attr"
			print(">>       appending {} into {}".format(src_path,dst_path))
			ncb_append(src_path,dst_path)

		shared_file = ""
		for file in created_files[k]["files"]:
			if "if.attr" in file:
				shared_file = file
				break
		if shared_file != "":
			for file in created_files[k]["files"]:
				if file != shared_file:
					dst_path = user["gb_path"] + "/targetspec/"+ border_folder+ "/" + file.split('/')[-2] + "/" + shared_file.split("/shared/")[1]
					slink = ("../shared/{} {}".format(shared_file.split("/shared/")[1],dst_path))
					ncb_slink(slink)
					#../shared/iad2-br-kct-p1-if.attr /home/joaq/GenevaBuilder/targetspec/border/iad2-br-kct-p1-r1/iad2-br-kct-p1-if.attr
	return gb_groups

#******************************************#
def create_aclmanage_mcm(peers,loopbacks,devices_br,devices_brick,devices_dx,bgp_prestaged,brick_operational):
	print("\n>> NOTE:\n   - BR-TRA that have APPLY-GROUP enabled, require the ACLManage MCM before the BGP Prestage.\n   - BR-TRA that have NOT APPLY-GROUP enabled, require the ACLManage MCM after the BGP Prestage.\n   - VC-COR have APPLY-GROUP enabled, but the ACLManage MCM is done after the BGP Prestage.\n   - BR-AGG does not require ACLManage for now on ClaymoreHD deployments.\n")

	if "vc-cor" in devices_brick[0] and not bgp_prestaged:
		required_mcm = False
		mcm_id = False
		return required_mcm,mcm_id

	if "br-agg" in devices_brick[0]:
		required_mcm = False
		mcm_id = False
		return required_mcm,mcm_id

	device_applygroup = []
	device_not_applygroup = []

	required_mcm = True
	mcm_id = False
	for device in devices_brick:
		if "-vc-cor-" in device:
			print(f"     Device {device} is VC-COR, so it has",bcolors.lightcyan,"APPLY-GROUP",bcolors.end)
			device_applygroup.append(device)

		else:
			for peer in peers:
				if device in peer:
					config = hercules.get_latest_config_for_device(device,"collected",['set-config'])

					if config:
						config = config.decode().replace(' ', '')
						if re.findall(r"PORTCULLIS",config):
							print(f"     Device {device} has",bcolors.lightcyan,"APPLY-GROUP",bcolors.end)
							device_applygroup.append(device)
							break
						else:
							print(f"     Device {device} has",bcolors.lightcyan,"NOT APPLY-GROUP",bcolors.end)
							device_not_applygroup.append(device)
							break
					else:
						print(f"     Device {device} not operational")
						break

	region = nsm.get_devices_region_from_nsm(devices_brick[0].split("-r")[0])[0]['NSM_Stack']
	command_bastion = f"ssh nebastion-{region.lower()} 'hostname'"
	print(f"\n   Looking for a Bastion in region {region.upper()}")
	try:
		output = subprocess.run(command_bastion, shell=True,stdout=PIPE, stderr=STDOUT)
		result = output.stdout.decode()
		neteng_bastion = re.findall(r"(neteng-bastion-.*.amazon.com)",result)[0]
		print(f"    Found {neteng_bastion}")
	except:
		print(f"    ERROR: unable to get neteng bastion for region {region}")
		return required_mcm,mcm_id

	if ((not bgp_prestaged and device_applygroup) or (bgp_prestaged and device_not_applygroup)) and "br-tra" in devices_brick[0]:
		if bgp_prestaged:
			devices_brick = device_not_applygroup
			bgp_prestage_done = "True"
		else:
			devices_brick = device_applygroup
			bgp_prestage_done = "False"
	elif "vc-cor" in devices_brick[0] and bgp_prestaged:
		bgp_prestage_done = "True"
	else:
		required_mcm = False
		mcm_id = False
		return required_mcm,mcm_id

	not_operational_devices_dx = []
	print(f"\n   Checking NSM status for DX Devices.")
	for device in devices_dx:
		result = nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
		if device not in result:
			print(f"    {device} is NOT Operational in NSM.")
			not_operational_devices_dx.append(device)
		else:
			print(f"    {device} is Operational in NSM.")

	#not_operational_devices_dx = devices_dx

	required_mcm = True
	dx_devices = []
	list_of_lags = []
	list_of_dx2_lags = []
	for brick_device in devices_brick:
		for peer in peers:
			device_a = peer.split("<>")[0]
			device_z = peer.split("<>")[1]
			lag = peers[peer]["ports"][0].split(",")[0]
			if brick_device == device_a and device_z in not_operational_devices_dx:
				if device_z not in dx_devices:
					#print(f"Adding {device_z} to list of DX devices")
					dx_devices.append(device_z)
				if 'bdr' in device_z and not lag in list_of_dx2_lags:
					list_of_dx2_lags.append(lag)
				elif not 'bdr' in device_z and not lag in list_of_lags:
					#print(f"Adding {lag} to list of lags")
					list_of_lags.append(lag)


	if not dx_devices:
		print(f"   All the DX devices are operational already, so no ACLManage MCM required.")
		required_mcm = False
		return required_mcm,mcm_id

	print(f"\n>> Running command to create ACLManage MCM using 'acl_manage_mcm.py' to the DX Devices that are not operational (wait 10 min):")

	if ((not bgp_prestaged and device_applygroup) or (bgp_prestaged and device_not_applygroup)) and "br-tra" in devices_brick[0]:
		if list_of_lags and list_of_dx2_lags:
			command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -brtra {} -ae {} -dae {} -bp {} -sb {}".format(",".join(dx_devices),",".join(devices_brick),",".join(list_of_lags),",".join(list_of_dx2_lags),bgp_prestage_done,neteng_bastion)
		elif list_of_lags:
			command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -brtra {} -ae {} -bp {} -sb {}".format(",".join(dx_devices),",".join(devices_brick),",".join(list_of_lags),bgp_prestage_done,neteng_bastion)
		elif list_of_dx2_lags:
			command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -brtra {} -dae {} -bp {} -sb {}".format(",".join(dx2_devices),",".join(devices_brick),",".join(list_of_dx2_lags),bgp_prestage_done,neteng_bastion)

	elif "vc-cor" in devices_brick[0] and bgp_prestaged:
		vccor_brick = re.findall("(.*-vc-cor-b[0-9]).*",devices_brick[0])[0]
		if brick_operational:
			if list_of_lags and list_of_dx2_lags:
				command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -vccor {} -ae {} -dae {} -sb {}".format(",".join(dx_devices),vccor_brick,",".join(list_of_lags),",".join(list_of_dx2_lags),neteng_bastion)
			elif list_of_lags:
				command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -vccor {} -ae {} -sb {}".format(",".join(dx_devices),vccor_brick,",".join(list_of_lags),neteng_bastion)
			elif list_of_dx2_lags:
				command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -vccor {} -dae {} -sb {}".format(",".join(dx_devices),vccor_brick,",".join(list_of_dx2_lags),neteng_bastion)
		else:
			if list_of_lags and list_of_dx2_lags:
				command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -vccor {} -ae {} -dae {} -sb {} -adv".format(",".join(dx_devices),vccor_brick,",".join(list_of_lags),",".join(list_of_dx2_lags),neteng_bastion)
			elif list_of_lags:
				command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -vccor {} -ae {} -sb {} -adv".format(",".join(dx_devices),vccor_brick,",".join(list_of_lags),neteng_bastion)
			elif list_of_dx2_lags:
				command = "/apollo/env/DXDeploymentTools/bin/acl_manage_mcm.py -pl {} -vccor {} -dae {} -sb {} -adv".format(",".join(dx_devices),vccor_brick,",".join(list_of_dx2_lags),neteng_bastion)


	print(bcolors.lightcyan,command,bcolors.end)
	try:
		output = subprocess.run(command, shell=True,stdout=PIPE, stderr=STDOUT)
		result = output.stdout.decode()
		print(result)
		mcm_id = re.findall(r"(MCM-[0-9]*) successfully updated",result)[0]
	except:
		print(f"   ERROR: unable to create MCM")

	return required_mcm,mcm_id




#############################################################################################################
##########################################  08. Tiedown functions  ##########################################
#############################################################################################################

#******************************************#
def tiedown_get_metro_igp():
	bgpmetroigp,sites = get_metro_igp()
	metroigp = {}#dictionary of sites with
	
	if bgpmetroigp != "" and sites!= "":
		bgpmetroigp = bgpmetroigp.split()
		for data in bgpmetroigp:
			if "METROHASCOMMONIGPLOCATIONEXCEPTIONS" in data:
				break
			if len(data) == 3:
				metroigp[data.lower()] = []

		sites = sites.split()
		sites = [x.replace("-br-cor-r1","") for x in sites]

		for metro in metroigp:
			for site in sites:
				if metro in site:
					metroigp[metro].append(site)
		#print(metroigp)

		bgpmetroigp = bgpmetroigp[bgpmetroigp.index("METROHASCOMMONIGPLOCATIONEXCEPTIONS")::]
		bgpmetroigp = [x.lower() for x in bgpmetroigp if len(x) > 3 and x != "METROHASCOMMONIGPLOCATIONEXCEPTIONS" and "#" not in x]
		#print(bgpmetroigp)

		for metro in metroigp:
			metroigp[metro] = [x for x in metroigp[metro] if x not in bgpmetroigp]
		return metroigp

#******************************************#
def tiedown_get(devices_brick,peers,loopbacks):
	tiedown = {}
	for peer in peers:
		if re.search(r"vc-cor",peer) and re.search(r"br-kct",peer) and peer.split("<>")[0] in devices_brick:
			pop = peer.split("-")[0]
			if pop not in tiedown:
				tiedown[pop] = {}
				tiedown[pop]["br-cor"] = search_border_peers(pop,"br-cor")
				tiedown[pop]["prefixes"] = []

			prefix = peers[peer]["p2p"].split(".")[:3]
			prefix = ".".join(prefix)+".0/24"

			if prefix not in tiedown[pop]["prefixes"]:
				tiedown[pop]["prefixes"].append(prefix)

	for device in loopbacks:
		if re.search(r"vc-cor",device) and device in devices_brick:
			pop = device.split("-")[0]
			if pop not in tiedown:
				tiedown[pop] = {}
				tiedown[pop]["br-cor"] = search_border_peers(pop,"br-cor")
				tiedown[pop]["prefixes"] = []

			prefix = loopbacks[device]["PRIMARYIP"].split(".")[:3]
			prefix = ".".join(prefix)+".0/24"
			if prefix not in tiedown[pop]["prefixes"]:
				tiedown[pop]["prefixes"].append(prefix)

	return tiedown

#******************************************#
def tiedown_missing(tiedown):
	#print("\n>>   ORIGINAL tiedown list to check: {}".format(json.dumps(tiedown,indent=4)))
	tiedown_missed = {}

	for pop in tiedown:
		brcor = tiedown[pop]["br-cor"][0]
		prefixes = tiedown[pop]["prefixes"]
		border_folder = muda_auxiliary.get_border_folder(pop)

		for prefix in prefixes:
			found_prefix = False
			command = 'grep \"{}\" {}/targetspec/{}/{}/*'.format(prefix,user["gb_path"],border_folder,brcor)

			#print("\nCOMMAND >>{}<<".format(command))
			try:
				output = subprocess.check_output(command, shell=True)
				#grep 150.222.224.0/24 /home/joaq/GenevaBuilder/targetspec/border/iad4-br-cor-r1/*
				result = output.decode()
				if prefix in result:
					found_prefix = True
				#print("\nResult:{}<<".format(result))
			except:
				#print("n>>   Not found existing tiedown for {} in {}.".format(prefix,brcor))
				pass


			if not found_prefix:
				if pop not in tiedown_missed:
					tiedown_missed[pop] = {}
					tiedown_missed[pop]["br-cor"] = tiedown[pop]["br-cor"]
					tiedown_missed[pop]["prefixes"] = []
					tiedown_missed[pop]["shared"] = ""
				tiedown_missed[pop]["prefixes"].append(prefix)

				command = 'ls {}/targetspec/{}/{} | grep tiedown | grep static | grep -v trio | grep -v bfb'.format(user["gb_path"],border_folder,brcor)

				#print("\nCOMMAND >>{}<<".format(command))
				try:
					output = subprocess.check_output(command, shell=True)
					#ll /home/joaq/GenevaBuilder/targetspec/border/iad4-br-cor-r1 | grep tiedown | grep static | grep -v trio | grep -v bfb
					result = output.decode()
					tiedown_missed[pop]["shared"] = result.split()[0]#static-iad-infra-tiedown.attr
				except:
					#print("n>>   Not found shared tiedown file in {}.".format(brcor))
					pass

	#print("\n>>   RESULTED missings tiedown: {}".format(json.dumps(tiedown_missed,indent=4)))
	return tiedown_missed


#******************************************#
def tiedown_create(tiedown,created_files):
	#print("\n>>   CREATE missings tiedown: {}".format(json.dumps(tiedown,indent=4)))
	tiedown_metro_igp = tiedown_get_metro_igp()
	#print("\n>>   List of MetroIGP for Tiedown creation:\n{}".format(tiedown_metro_igp))

	any_pop = list(tiedown.keys())[0]#gets a pop from the tiedown
	border_folder = muda_auxiliary.get_border_folder(any_pop)

	directory_shared = "{}/MUDA/GenevaBuilder/targetspec/{}/shared".format(user["muda_path"],border_folder)
	if not os.path.exists(directory_shared):
		os.makedirs(directory_shared)

	for pop in tiedown:
		if ".attr" in tiedown[pop]["shared"]:
			#brcor = tiedown[pop]["br-cor"][0]
			brcor = muda_auxiliary.regex_from_list(tiedown[pop]["br-cor"])

			created_files[brcor] = {}
			created_files[brcor]["type"]="GB append"
			created_files[brcor]["files"]=[]

			attr = "{}/{}".format(directory_shared,tiedown[pop]["shared"])

			if pop in attr:
				#print(">>   TC name is in the tiedown file name, checking if metro IGP exists.")
				metro_area = ""
				for metro in tiedown_metro_igp:
					if pop in tiedown_metro_igp[metro]:
						metro_area = metro

				if metro_area != "":
					tiedown_metro_igp[metro_area].remove(pop)
					for metro_pop in tiedown_metro_igp[metro_area]:
						#print(">>   We also need the tiedown in {} because it is a metro wide IGP.".format(metro_pop))

						metro_brcor_list = search_border_peers(metro_pop,"br-cor")
						metro_brcor_regex = muda_auxiliary.regex_from_list(metro_brcor_list)
						metro_brcor = metro_pop + "-br-cor-r1"

						command = 'ls {}/targetspec/{}/{} | grep tiedown | grep static | grep -v trio | grep -v bfb'.format(user["gb_path"],border_folder,metro_brcor)
						#print("\nCOMMAND >>{}<<".format(command))
						try:
							output = subprocess.check_output(command, shell=True)
							#ll /home/joaq/GenevaBuilder/targetspec/border/iad4-br-cor-r1 | grep tiedown | grep static | grep -v trio | grep -v bfb
							result = output.decode()
							metro_attr = "{}/{}".format(directory_shared,result.split()[0])#static-iad-infra-tiedown.attr

							created_files[metro_brcor_regex] = {}
							created_files[metro_brcor_regex]["type"]="GB append"
							created_files[metro_brcor_regex]["files"]=[]
							created_files[metro_brcor_regex]["files"].append(metro_attr)
							f = open(metro_attr, "w")
							f.write("\n")
							prefixes = tiedown[pop]["prefixes"]
							for prefix in prefixes:
								f.write('STATICROUTE {} DESC "Static tie down for {} Infra Space"\n'.format(prefix,pop))
								f.write('STATICROUTE {} DISCARD\n'.format(prefix))
								f.write('STATICROUTE {} COMMUNITY 65030:0\n'.format(prefix))
							f.close()

						except:
							pass

			created_files[brcor]["files"].append(attr)
			f = open(attr, "w")
			f.write("\n")

			prefixes = tiedown[pop]["prefixes"]
			for prefix in prefixes:
				f.write('STATICROUTE {} DESC "Static tie down for {} Infra Space"\n'.format(prefix,pop))
				f.write('STATICROUTE {} DISCARD\n'.format(prefix))
				f.write('STATICROUTE {} COMMUNITY 65030:0\n'.format(prefix))
			f.close()

		else:
			print(bcolors.red,"\n>>   Not found shared tiedown file for PoP {}.".format(pop.upper()),bcolors.end)

	return created_files


#############################################################################################################
##########################################  10. CR creators  ################################################
#############################################################################################################



def create_cr(brick_groups,peers,vccors,gb_path,tiedown,next_step):
	brick_groups.sort()
	
	list_vccors = [x for x in brick_groups if "-vc-cor-" in x]
	list_brkcts = [x for x in brick_groups if "-br-kct-" in x]
	list_brcors = [x for x in brick_groups if "-br-cor-" in x]
	list_brtras = [x for x in brick_groups if "-br-tra-" in x]
	list_braggs = [x for x in brick_groups if "-br-agg-" in x]
	list_pop = list(set([x.split("-")[0] for x in brick_groups]))

	
	if list_brtras != []:
		cr_title = "[DX][MUDA][{}] DXPEER attributes for BR-TRA".format("/".join(list_pop).upper())
		dockets = "IED-BR-TRA"
	elif list_braggs != []:
		cr_title = "[DX][MUDA][{}] Customer VPC attributes and prefix list on BR-AGG".format("/".join(list_pop).upper())
		dockets = "Regional-Border-Deploy"
	else:
		cr_title = "[DX][MUDA][{}] attributes for VC-COR brick".format("/".join(list_pop).upper())
		dockets = "dx-deploy"

	if list_brcors != []:
		dockets += ",Isd-bb"
		cr_title += " with static tiedown"
	if list_brkcts != []:
		dockets += ",Regional-Border-Deploy"

	print(f"   MUDA format group of devices: {brick_groups}")
	brick_groups_new = []
	for group in brick_groups:
		stem = group.split("r[")[0]
			
		list_devices = mcm.mcm_get_hostnames_from_regex(group)
		list_numbers = []
		for device in list_devices:
			for peer in peers:
				if device in peer or "br-cor" in device:
					list_numbers.append(device.replace(stem,""))
					break
		new_regex = stem + "(" + "|".join(list_numbers) + ")$"
		#print(new_regex)#fra50-br-tra-(r1|r2|r3|r4)$
		brick_groups_new.append(new_regex)
	brick_groups = brick_groups_new
	#if "-br-agg-" in stem:#On BR-AGG we use the entire region due to changes in PrefixList which affects the entire region
	#	brick_groups = [f"{region}.*-br-agg-r.*"]#region is not defined yet!
	print(f"   Regex format group of devices: {brick_groups}")



	commit_command = "git commit -m '" + cr_title + "'"
	print(bcolors.lightcyan,"        GB running: git add .",bcolors.end)
	print(bcolors.lightcyan,f"        GB running: {commit_command}",bcolors.end)
	cr.genevabuilder_git_add_commit(gb_path,commit_command)

	command = '/apollo/env/ReleaseWorkflowCLI/bin/generate_configs.py --devices "{}" --cr --dockets {}'.format("|".join(brick_groups),dockets)
	print(bcolors.lightcyan,f"        GB running: {command}",bcolors.end)
	print("        Please wait 20 minutes")
	
	gb_cr = cr.genevabuilder_generate_configs(gb_path,command)

	if gb_cr:
		print("     Please review and publish your CR:")
		print(bcolors.lightblue,"     https://code.amazon.com/reviews/{}\n".format(gb_cr),bcolors.end)
		print(bcolors.red,"\n>> WARNING: before publishing your CR, review the diffs and do the IP validations on any new IP in the CR.\n   Look for your Step number and follow instuctions: https://w.amazon.com/bin/view/DXDEPLOY/Runbooks/MUDA/",bcolors.end)
	
		merge_command = '/apollo/env/GitLocker/bin/gitlocker.py --devices "{}" --cr {}'.format("|".join(brick_groups),gb_cr)
		#print(bcolors.lightblue,"     git pull --rebase",bcolors.end)
		release_command = '/apollo/env/ReleaseWorkflowCLI/bin/release_configs.py --devices "({})-(br-(dcr|ubq|cor|rrr|tra|bib|lle|sbc)|en-(tra|gct))-.*" -ro'.format("|".join(list_pop))

		#New way to release config in GB
		#"/apollo/env/ReleaseWorkflowCLI/bin/release_configs.py --devices 'jfk6-vc-cor-b1-r[1234]' --repository GenevaBuilder"

		for brick in list_vccors + list_brtras + list_braggs:
			ddb_table_update(brick,next_step,True,gb_cr,merge_command,release_command,tiedown)

			if next_step == 19:
				print("\n        IMPORTANT: when you merge this CR, you are blocking all the Border teams to do any work on these BR-KCT, because BR-KCT is bolted.")
				print("           RBE allows 3 days from the time you merge this CR, to the time you run the VC-COR Turn-Up MCM to push the changes.")
				print("           Only MERGE this CR when you are ready to work on the next steps: provisioning, mobius and VC-COR Turn-Up MCM.")

	return

#############################################################################################################
##########################################  11. MUDA show and auto  #########################################
#############################################################################################################

#******************************************#
def check_border_device_ready(stream,device,vccor):
	"""
	Returns:
	0 PENDING
	1 OK
	2 OK (NOT Operational/Maintenance)
	3 OK (Failed to retrieve NSM)
	"""
	if stream == 'released':
		config = hercules.get_latest_config_for_device(device,"released")
		if config != None:
			config = config.decode().replace(' ', '')
			if re.findall(r'description"{}"'.format(vccor),config):
				return 1
	elif stream == 'collected':
		config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
		if config != None:
			config = config.decode().replace(' ', '')
			if re.findall(r'description{}'.format(vccor),config):
				return 1
	#print(f"Config for {device} {stream} not found in Hercules , checking NSM")
	try:
		device_operational = nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
		if device not in device_operational:
			return 2 #because it is NOT OPERATIONAL in NSM
	except Exception as e:
		print(f"{device} error retrieving from NSM: {e}")
		return 3 #because it is failing NSM
	return 0

#******************************************#
def create_var_file_turnup(vccor_to_prestage,border_regex,var_file_name,peers,loopbacks):
	vccor_to_prestage_regex = muda_auxiliary.regex_from_list(vccor_to_prestage)

	print(f"\n        Gathering 'peers' and 'loopbacks' from Bricks {vccor_to_prestage_regex}.")
	peers = {}
	loopbacks = {}
	muda_table = ddb.get_ddb_table('muda_table')
	for vccor_brick in vccor_to_prestage_regex.split("|"):
		peers.update(ddb.get_device_from_table(muda_table, 'brick', vccor_brick)['peers'])
		loopbacks.update(ddb.get_device_from_table(muda_table, 'brick', vccor_brick)['loopbacks'])
	#print(f"\n\n\nPEERS AFTER COMBINATION: {peers}")
	#print(f"\n\n\nLOOPBACKS AFTER COMBINATION: {loopbacks}")

	if peers == {}:
		return False

	print("\n        Creating VAR file:\n")
	pop = border_regex.split("-")[0]
	var_file = f"""TC={pop}
NSM_CM=MCM-00000000
NSM_UPDATED_BY={user["username"]}
ENABLE_VC_COR_TURNUP=true
ENABLE_BIB_TURNUP=false
ENABLE_COR_TURNUP=false
ENABLE_DCR_TURNUP=false
ENABLE_GCT_TURNUP=false
ENABLE_LLE_TURNUP=false
ENABLE_TRA_TURNUP=false
ENABLE_UBQ_TURNUP=false
ENABLE_EN_TRA_TURNUP=false
ENABLE_ZTP_TRA_TURNUP=false
ENABLE_TRA_TURNUP_SLA_R1_PRESENT=false
ENABLE_TRA_TURNUP_SLA_R2_PRESENT=false
BR_SLA_IFACES=
CHECK_UNLABELLED_LO=true
NSM_ILS_UPDATE=true
TEAM_CATEGORY=AWS
TEAM_TYPE=DirectConnect
TEAM_ITEM=RouterHealth"""

	############ Loopbacks and P2P IP addresses on VC-COR
	file_loopbacks = []
	file_unlabeled = []
	file_p2p = []

	brkct_to_prestage = mcm.mcm_get_hostnames_from_regex(border_regex)
	if len(vccor_to_prestage) <= 8:
		counter = 1

		for x in vccor_to_prestage:
			file_loopbacks.append(loopbacks[x]['PRIMARYIP'] + "/32")
			file_unlabeled.append(loopbacks[x]['UNLABELEDLOOPIP'])
			new_device = []
			file_ports = []
			for y in brkct_to_prestage:
				peer = x + "<>" + y
				p2p_ip = peers[peer]['p2p']
				ports = peers[peer]['ports']
				for port in ports:
					file_ports.append(port.split(",")[0])
					file_ports.append(port.split(",")[1])
				file_p2p.append(p2p_ip)

			file_ports = list(dict.fromkeys(file_ports))
			file_ports.sort()
			my_ports = ",".join(file_ports)

			var_file = var_file + f"""
NEW_DEVICE_{counter}={x}
NEW_DEVICE_{counter}_TURNUP=true"""
			counter += 1

		for k in range(counter,9):
			var_file = var_file + f"""
NEW_DEVICE_{k}_TURNUP=false"""

		text1 = ",".join(file_loopbacks) + "," +  ",".join(file_p2p)
		var_file = var_file + f"""
NEW_IPS={text1}
UNLABELLED_LOOPBACKS={",".join(file_unlabeled)}
NEW_DEVICE_INTERFACES={my_ports}"""

		############ BR-KCT INTERFACES
		brktc_r1 = brkct_to_prestage[0]
		brkct_ports = []
		for x in vccor_to_prestage:
			peer = x + "<>" + brktc_r1
			ports = peers[peer]['ports']
			for port in ports:
				brkct_ports.append(port.split(",")[2])	
				brkct_ports.append(port.split(",")[3])

		brkct_ports = list(dict.fromkeys(brkct_ports))
		var_file = var_file + f"""
KCT_INTERFACES={",".join(brkct_ports)}"""

		print(var_file)
		file = user["muda_path"]+"/MUDA/"+var_file_name
		f = open(file, "w")
		f.write(var_file)
		f.close()
		return True


#******************************************#
def create_var_file_normalization(lags_to_normalize,border_regex,var_file_name):
	lags_to_normalize.sort()

	print("\n        Creating VAR file:\n")
	var_file = """ENABLE_VC_COR_NORMALIZATION=true
ENABLE_BIB_NORMALIZATION=false
ENABLE_COR_NORMALIZATION=false
ENABLE_TRA_NORMALIZATION=false
ENABLE_COR_1_NORMALIZATION=false
ENABLE_COR_2_NORMALIZATION=false
ENABLE_COR_3_NORMALIZATION=false
ENABLE_COR_4_NORMALIZATION=false
ENABLE_TRA_1_NORMALIZATION=false
ENABLE_TRA_2_NORMALIZATION=false
ENABLE_TRA_3_NORMALIZATION=false
ENABLE_TRA_4_NORMALIZATION=false
NEW_COR_1=false
NEW_COR_2=false
NEW_COR_3=false
NEW_COR_4=false"""

	device = mcm.mcm_get_hostnames_from_regex(border_regex)[0]
	device_numbers = [str(x) for x in range(1,13)]
	try:
		config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
		if config != None:
			config = config.decode().replace(' ', '')
			config = config.replace('\n', '')
			for lag in lags_to_normalize:
				port_list = re.findall(r'description"{}{}(xe|et)-[0-9]*/[0-9]*/[0-9:]*-->(xe|et)-[0-9]*/[0-9]*/[0-9:]*ae[0-9]*([\w-]*)"setinterfaces'.format(device,lag),config)
				if port_list != []:
					vccor = port_list[0][-1]
					vccor_number = vccor.split("-r")[1]
					var_file = var_file + f"""
ENABLE_VCCOR_{vccor_number}_NORMALIZATION=true
NEW_VCCOR_{vccor_number}_NAME={vccor}
NEW_VCCOR_{vccor_number}_AE_INT={lag}
LINKS_PER_AE_INT_{vccor_number}={len(port_list)}"""
					device_numbers.remove(vccor_number)
				else:
					print(f"        LAG {lag} not found in {device} collected config, VAR file not created")
					return False
		else:
			print(f"        No Hercules config received for {device}, VAR file not created")
			return False
	except:
		print(f"        Unable to retrieve Hercules config for {device}, VAR file not created")
		return False
	
	print(var_file)
	file = user["muda_path"]+"/MUDA/"+var_file_name
	f = open(file, "w")
	f.write(var_file)
	f.close()
	return True

#******************************************#
def create_var_file_tiedown(tc,list_of_prefixes,supernet):
	brtra_list = nsm.get_devices_from_nsm(f"{tc}-br-tra",state = ['OPERATIONAL','MAINTENANCE'])
	brtra_list.sort(key=lambda x: int(x.split("-r")[-1]))
	brtra = brtra_list[0]

	config = hercules.get_latest_config_for_device(brtra,"collected",['set-config'])
	if config != None:
		config = config.decode().replace(' ', '')
		try:
			local_transit_peer = str(IPNetwork(re.findall(r'setgroupsAUTO-LASSI-STATICSrouting-optionsstaticroute.*next-hop([\d\.]+)',config)[0])[0])
		except Exception as e:
			print(bcolors.red+f"\n     Error getting LOCAL_TRANSIT_PEER for VAR file: {e}"+bcolors.end)
			print("     MUDA was trying to create the VAR file for the Tiedown MCM")
			print("     More info in https://w.amazon.com/bin/view/Networking/NetworkDeployment/IS-Deployment/ahmenasr/VC-COR-prestage-BB/")
			print("     However, it was unable to automtically find that IP.")
			print(f"     To continue, please enter a transit peer IP address from {brtra}")
			local_transit_peer = input("     LOCAL_TRANSIT_PEER = ") or " "

		tiedown_var_file = f"""ADD_INFRA_TIEDOWN=True
ADD_PREFIX_ACTIVE=False
ADD_TAZZY_TIEDOWN=False
ADD_TRIO_TIEDOWN=False
AP_COR=sin2-br-cor-r2
BORDER_INFRA_SUPERNET_PREFIX={supernet}
BORDER_INFRA_SUPERNET_PREFIX_ACTIVE={supernet}
DOGFISH_REGION=iad
DOGFISH_REGION_CHECK=false
EU_COR=dub2-br-cor-r2
LOCAL_COR={tc}-br-cor-r1
LOCAL_TRA={brtra}
LOCAL_TRANSIT_PEER={local_transit_peer}
NA_COR=jfk6-br-cor-r1
PDMS_STACK=prod
SA_COR=gru1-br-cor-r2
SITE_BORDER_INFRA_PREFIX={list_of_prefixes}
SITE_PREFIX_ACTIVE={list_of_prefixes}
"""

		print(f"Tiedown VAR file created:\n{tiedown_var_file}")
		var_file_name = "{}_tiedown.var".format(tc)
		var_file = user["muda_path"]+ "/MUDA/" + var_file_name
		with open(var_file, 'w') as file:
			file.write(tiedown_var_file)
		return var_file

	else:
		print(f"        Unable to retrieve hercules collected configuration from {brtra}")
		return False


#******************************************#
def muda_stats():
	"""
	Show deployment logs
	"""
	muda_table = ddb.get_ddb_table('muda_table')
	muda_dict = ddb.scan_full_table(muda_table)
	muda_dict = sorted(muda_dict, key = lambda x: (x['progress'],x['brick']))
	gb_path = user["gb_path"]

	work_types = {
	'gb_port_reservation_cr':{'description':'Port Reservation CR','loe_unit':2,'total':[]},
	'gb_port_reservation_mcm':{'description':'Port Reservation MCM','loe_unit':4,'total':[]},
	'dx_port_reservation_mcm':{'description':'DX Port Reservation MCM','loe_unit':4,'total':[]},
	'gb_cr':{'description':'GenevaBuilder CR','loe_unit':6,'total':[]},
	'manualpcn':{'description':'ManualPCN or Tiedown MCM','loe_unit':4,'total':[]},
	'mcm_border_prestage':{'description':'Border Prestage MCM','loe_unit':6,'total':[]},
	'mcm_border_normalization':{'description':'Border Normalization MCM','loe_unit':4,'total':[]},
	'mcm_aclmanage':{'description':'ACLManage MCM','loe_unit':6,'total':[]},
	}

	lead_nde = []
	dx_vccor = []
	dx_phoenix = []
	dx_centennial = []
	dx_heimdall = []
	dx_vcdar = []

	for brick in muda_dict:
		if brick.get('time'):
			logs = brick['time']
			list_nde = re.findall(r"\) by ([a-z]*) > ",logs)
			for nde in list_nde:
				if nde not in lead_nde:
					lead_nde.append(nde)

		if "vc-cor" in brick['brick'] and brick['brick'] not in dx_vccor:
			dx_vccor.append(brick['brick'])

		if brick.get('dx'):
			dx_deployments = brick.get('dx').split("|")
			for dx_deployment in dx_deployments:
				if re.findall("-vc-car-.*-v2-",dx_deployment):
					if dx_deployment not in dx_centennial:
						dx_centennial.append(dx_deployment)
				if re.findall("-vc-car-.*-v3-",dx_deployment):
					if dx_deployment not in dx_phoenix:
						dx_phoenix.append(dx_deployment)
				if re.findall("-vc-car-.*-v4-",dx_deployment):
					if dx_deployment not in dx_heimdall:
						dx_heimdall.append(dx_deployment)
				if re.findall("-vc-car-.*-v5-",dx_deployment):
					if dx_deployment not in dx_heimdall:
						dx_heimdall.append(dx_deployment)
				if re.findall("-vc-dar-",dx_deployment):
					if dx_deployment not in dx_vcdar:
						dx_vcdar.append(dx_deployment)

		for work_type in work_types:
			list_work_type = brick.get(work_type)
			if list_work_type:
				#work_types[work_type]['total'] += list_work_type.split(",")

				if "MCM" in work_types[work_type]['description']:
					listed_mcms = list_work_type.split(",")
					#print(f"\nFound MCMs for this deployment: {listed_mcms}")
					for mcm in listed_mcms:
						cm_friendly_id = CmFriendlyIdentifier(friendly_id=mcm)
						uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
						cm_status = uuid.cm.status_and_approvers.cm_status
						if cm_status in ["Completed"] and mcm not in work_types[work_type]['total']:
							work_types[work_type]['total'].append(mcm)
							#print(f"https://mcm.amazon.com/cms/{mcm}")

				elif "CR" in work_types[work_type]['description']:
					listed_gbcrs =list_work_type.split(",")
					#print(f"\nFound CRs for this deployment: {listed_gbcrs}")
					for gbcrs in listed_gbcrs:
						if cr.cr_status_closed(gb_path,gbcrs):
							work_types[work_type]['total'].append(gbcrs)
							#print(f"https://code.amazon.com/reviews/{gbcrs}")

	lead_nde.sort()
	print(bcolors.lightgreen,f">> MUDA was used by {len(lead_nde)} NDEs",bcolors.end,f"{lead_nde}\n")
	print("Average LOE is 12 hours per deployment below, for IP allocations (P2P/CSC/Inet/Loopbacks), DNS entry creation, adding devices, cabling and links to Jukebox for each.")
	print(bcolors.lightcyan,f"> {len(dx_vccor)} VC-COR brick deployments: ",bcolors.end,f"{dx_vccor}")
	print(bcolors.lightcyan,f"> {len(dx_centennial)} Centennial deployments: ",bcolors.end,f"{dx_centennial}")
	print(bcolors.lightcyan,f"> {len(dx_phoenix)} Phoenix deployments: ",bcolors.end,f"{dx_phoenix}")
	print(bcolors.lightcyan,f"> {len(dx_heimdall)} Heimdall deployments: ",bcolors.end,f"{dx_heimdall}")
	print(bcolors.lightcyan,f"> {len(dx_vcdar)} VC-DAR deployments: ",bcolors.end,f"{dx_vcdar}")
	ip_allocation_loe = len(dx_vccor) + len(dx_centennial) + len(dx_phoenix) + len(dx_heimdall) + len(dx_vcdar)
	print(bcolors.lightgreen,f">> LOE saved on IP allocations, DNS entries and Jukebox work: {ip_allocation_loe*12} hours > {round((ip_allocation_loe*12)/8,2)} days > {round(((ip_allocation_loe*12)/8)/5,2)} weeks\n\n",bcolors.end)

	print("List of Merged CRs and Completed MCMs created by MUDA. The ACLManage MCM are created by acl_manage_mcm.py.")
	total_loe = 0
	for work_type in work_types:
		total_loe += work_types[work_type]['loe_unit'] * len(work_types[work_type]['total'])
		print(bcolors.lightcyan,f"> {len(work_types[work_type]['total'])} * {work_types[work_type]['loe_unit']} hours, LOE on {work_types[work_type]['description']}: ",bcolors.end,f"{work_types[work_type]['total']}")
	print(bcolors.lightgreen,f">> LOE saved on CR and MCM creation: {total_loe} hours > {round(total_loe/8,2)} days > {round(total_loe/40,2)} weeks",bcolors.end)

	full_loe = total_loe/40 + ((ip_allocation_loe*12)/8)/5
	print(bcolors.lightgreen,f"\n\n>> MUDA saved {round(full_loe, 2)} weeks of NDE work.")


#******************************************#
def muda_log(regex):
	"""
	Show deployment logs
	"""
	muda_table = ddb.get_ddb_table('muda_table')
	muda_dict = ddb.scan_full_table(muda_table)

	muda_dict = [x for x in muda_dict if regex in x['brick']]
	muda_dict = sorted(muda_dict, key = lambda x: (x['progress'],x['brick']))

	#print(muda_dict)
	data = []
	pos = 1

	for brick in muda_dict:
		if "vc-cor" in brick['brick']:
			print(bcolors.lightcyan,"\n>> {}:".format(brick['brick']),bcolors.end,"\n{}".format(brick['time']))
		elif "br-tra" in brick['brick']:
			print(bcolors.lightgreen,"\n>> {}:".format(brick['brick']),bcolors.end,"\n{}".format(brick['time']))
		else:
			print(bcolors.pink,"\n>> {}:".format(brick['brick']),bcolors.end,"\n{}".format(brick['time']))

#******************************************#
def muda_show(regex):
	"""
	Checks the muda_table in DDB and automatically updates steps.
	"""
	muda_table = ddb.get_ddb_table('muda_table')
	muda_dict = ddb.scan_full_table(muda_table)

	muda_dict = [x for x in muda_dict if regex in x['brick']]
	muda_dict = sorted(muda_dict, key = lambda x: (x['progress'],x['brick']))

	#print(muda_dict)
	data = []
	pos = 1

	for brick in muda_dict:
		timestamp = brick.get('time')
		if timestamp:
			timestamp = timestamp.split("\n")[-1]
			timestamp_formatted = timestamp.split(" > ")
			if len(timestamp_formatted) == 3:
				timestamp = f'{timestamp_formatted[0]}{timestamp_formatted[1].split(")")[1]}'

		if "vc-cor" in brick['brick']:
			row = [bcolors.lightcyan+brick['brick']+bcolors.end,bcolors.lightcyan+f"{int(brick.get('progress')):02d}"+bcolors.end,timestamp,brick.get('comment'),brick.get('br'),brick.get('dx'),brick.get('cutsheet_mcm'),brick.get('gb_port_reservation_cr'),brick.get('gb_port_reservation_mcm'),brick.get('dx_port_reservation_mcm'),brick.get('port_shutdown_mcm'),brick.get('gb_cr'),brick.get('manualpcn'),brick.get('mcm_border_prestage'),brick.get('mcm_border_normalization'),brick.get('mcm_aclmanage'),brick.get('mcm_ibgp_mesh'),brick.get('mcm_ixops_handoff')]
		elif "br-tra" in brick['brick']:
			row = [bcolors.lightgreen+brick['brick']+bcolors.end,bcolors.lightgreen+f"{int(brick.get('progress')):02d}"+bcolors.end,timestamp,brick.get('comment'),brick.get('br'),brick.get('dx'),brick.get('cutsheet_mcm'),brick.get('gb_port_reservation_cr'),brick.get('gb_port_reservation_mcm'),brick.get('dx_port_reservation_mcm'),brick.get('port_shutdown_mcm'),brick.get('gb_cr'),brick.get('manualpcn'),brick.get('mcm_border_prestage'),brick.get('mcm_border_normalization'),brick.get('mcm_aclmanage'),brick.get('mcm_ibgp_mesh'),brick.get('mcm_ixops_handoff')]
		else:
			row = [bcolors.pink+brick['brick']+bcolors.end,bcolors.pink+f"{int(brick.get('progress')):02d}"+bcolors.end,timestamp,brick.get('comment'),brick.get('br'),brick.get('dx'),brick.get('cutsheet_mcm'),brick.get('gb_port_reservation_cr'),brick.get('gb_port_reservation_mcm'),brick.get('dx_port_reservation_mcm'),brick.get('port_shutdown_mcm'),brick.get('gb_cr'),brick.get('manualpcn'),brick.get('mcm_border_prestage'),brick.get('mcm_border_normalization'),brick.get('mcm_aclmanage'),brick.get('mcm_ibgp_mesh'),brick.get('mcm_ixops_handoff')]
		data.append(row)
		pos += 1

	pd = pandas.DataFrame(data,list(range(1,pos)))
	table = prettytable.PrettyTable([''] + list(["Brick","Step","Last change","Comment","Border side","DX side","Cutsheet MCM","BR Port Reservation CR","BR Port Reservation MCM","DX Port Reservation MCM","Port Shutdown MCM","Brick GB attributes CR","ManualPCN MCM","BR Prestage MCM","BR Normalization MCM","ACLManage MCM","iBGP Mesh MCM","IXOps Handoff MCM"]))

	table.align["Brick"] = "l"
	table.align["Last change"] = "l"
	table.align["Comment"] = "l"
	table.align["Border side"] = "l"
	table.align["DX side"] = "l"
	table.align["Cutsheet MCM"] = "l"
	table.align["BR Port Reservation CR"] = "l"
	table.align["BR Port Reservation MCM"] = "l"
	table.align["DX Port Reservation MCM"] = "l"
	table.align["Port Shutdown MCM"] = "l"
	table.align["Brick GB attributes CR"] = "l"
	table.align["ManualPCN MCM"] = "l"
	table.align["BR Prestage MCM"] = "l"
	table.align["BR Normalization MCM"] = "l"
	table.align["ACLManage MCM"] = "l"
	table.align["iBGP Mesh MCM"] = "l"
	table.align["IXOps Handoff MCM"] = "l"

	for row in pd.itertuples():
		table.add_row(row)
	print(table)

	return True


#******************************************#
def muda_auto(regex,peers,vccors,loopbacks,df,bgp_communities,modeledcm):
	"""
	Checks the muda_table in DDB and allows you to do the next manual step for each deployment.
	"""
	muda_table = ddb.get_ddb_table('muda_table')
	muda_dict = ddb.scan_full_table(muda_table)
	muda_dict = [x for x in muda_dict if regex in x['brick']]
	muda_dict = sorted(muda_dict, key = lambda x: (x['progress'],x['brick']))

	for brick in muda_dict:

		#TESTING SPECIFIC STEP
		#brick['progress'] = 9
		
		devices_br = mcm.mcm_get_hostnames_from_regex(brick['br'])
		devices_brick = mcm.mcm_get_hostnames_from_regex(brick['brick'])
		devices_dx = mcm.mcm_get_hostnames_from_regex(brick['dx'])
		loopbacks = brick.get('loopbacks')
		peers = brick.get('peers')
		waiting_cr_mcm_completion = brick.get('waiting_cr_mcm_completion')

		print(bcolors.lightcyan,f"\n>> {brick['brick']} (step {brick['progress']}): {brick['comment']}",bcolors.end)

		##########################################################################################
		# 08 == Port Reservation CR.
		if int(brick['progress']) == 8:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				gb_cr = brick['gb_port_reservation_cr'].split(",")[-1]
				merge_command = brick['merge_command']
				gb_path = user["gb_path"]
				print("\n        MUDA checks if the CR is merged in your local GB repo, so make sure that your GB repo is updated after the merge.")
				if cr.cr_status_closed(gb_path,gb_cr):
					print(f"        The {gb_cr} is already merged, moving to the next step.")
					ddb_table_update(brick['brick'],9,False) # waiting_cr_mcm_completion is False
				else:
					print(f"        The {gb_cr} is not merged yet.")
					print("        When it is approved, please merge it with:")
					print(bcolors.lightblue,"     {}".format(merge_command),bcolors.end)
			
			#The CR/MCM was not created yet:
			else:
				print(f"        Devices BR: {devices_br}\n        Devices Brick: {devices_brick}\n        Devices DX: {devices_dx}\n")

				print(f"        Checking NSM state for Brick {brick['brick']}.")
				result = nsm.get_devices_from_nsm(devices_brick[0],state = ['OPERATIONAL','MAINTENANCE'])

				if result == []:
					print(f"        Brick {brick['brick']} is NOT Operational/Maintenance.\n")
					parents = devices_br
					parents_regex = brick['br']
					children = devices_brick
					children_regex = brick['brick']
					flip_peer = True#flip the order because the parent is on the right side of the peer
				else:
					print(f"        Brick {brick['brick']} is Operational/Maintenance.\n")
					parents = devices_brick
					parents_regex = brick['brick']
					children = devices_dx
					children_regex = brick['dx']
					flip_peer = False
			
				for device_type in muda_data["port_reservation_cr"]:
					if re.findall(device_type,parents_regex):
						method = muda_data["port_reservation_cr"][device_type]
						break
				tool = method["tool"]
				print(f"        The port reservation will be done in {tool}.")

				if "GenevaBuilder" in tool:
					gb_path = os.path.expanduser("~")+"/"+tool
					print(bcolors.lightcyan,f"\n        {tool}: git status",bcolors.end)
					if cr.genevabuilder_git_status_ready(gb_path):
						print(f"        Your {tool} repository is clean.")
						
						print(bcolors.lightcyan,f"        {tool}: git pull --rebase",bcolors.end)
						cr.genevabuilder_git_pull(gb_path)
						print(f"\n        Your {tool} repository is updated now.")

						print("\n")
						reservations = {}
						if peers != {}:
							port_reservations = {}
							for peer in peers:
								if flip_peer:
									peer_parent = peer.split("<>")[1]
									peer_child = peer.split("<>")[0]
								else:
									peer_parent = peer.split("<>")[0]
									peer_child = peer.split("<>")[1]
								new_line = ""

								if peer_parent in parents and peer_child in children:
									#print(f"\n        Checking port reservations for peer {peer}: {peers[peer]}.")
									config = hercules.get_latest_config_for_device(peer_parent,'collected',['set-config'])

									if config != None:
										config = config.decode().replace(' ', '')
										config = config.lower()
									else:
										print(f"        Unable to retrieve hercules collected configuration from {peer_parent}")
										answer = input(f"        Is {peer_parent} not Operational yet, but you want to continue reserving the ports? (y/n)? [n]: ") or "n"
										if answer == "y":
											config = ""

									if config != None:
										port_list = peers[peer]["ports"]
										reserve_lag = False
										for port in port_list:
											if flip_peer:
												parent_lag = port.split(',')[3]
												parent_port = port.split(',')[2]
												child_port = port.split(',')[1]
												child_lag = port.split(',')[0]
											else:
												parent_lag = port.split(',')[0]
												parent_port = port.split(',')[1]
												child_port = port.split(',')[2]
												child_lag = port.split(',')[3]
											pattern = ".*interfaces"+parent_port+"description.*"+peer_child+".*"
											if not re.findall(pattern,config):
												new_line += f'IFDESC {parent_port} "RESERVED: DX tt/NA {user["username"]} - {peer_parent} {parent_lag} {parent_port} > {child_port} {child_lag} {peer_child}"\n'
												reserve_lag = True
										pattern = ".*interfaces"+parent_lag+"description.*"
										if not re.findall(pattern,config) and reserve_lag and method["unitlag"] != []:
											if '-vc-bdr-' in peer_child:
												new_line += f'IFACE L3 {parent_lag} DESC "RESERVED: AS7224-{peer_child}"\n'
												new_line += f'IFACE L3 {parent_lag} UNIT 0\n'
											else:
												new_line += f'IFACE L3 {parent_lag} DESC "RESERVED: AS7224-{peer_child}"\n'
												for unit in method["unitlag"]:
													new_line += f'IFACE L3 {parent_lag} UNIT {unit}\n'
							
									if new_line != "":
										print(f"        Port reservation required for {peer}:\n{new_line}")
										if not port_reservations.get(peer_parent):
											port_reservations[peer_parent] = new_line
										else:
											port_reservations[peer_parent] += new_line
									else:
										print(f"        Port reservation not required for {peer}")

							if port_reservations != {}:
								#print(port_reservations)
								print(f"\n        Creating GB attributes:\n")

								any_parent = list(port_reservations.keys())[0]
								border_folder = muda_auxiliary.get_border_folder(any_parent)

								for parent in port_reservations:
								
									parent_path = gb_path+"/targetspec/" + border_folder
									for splitter in method["gbfolders"]:
										found = re.findall(splitter,parent)[0]
										parent_path += "/" + parent.split(found)[0] + found
									if not os.path.exists(parent_path):
										print(f"        Error: directory {parent_path} doesn't exist.")
										break
								
									attr = parent_path + "/{}-if-port_reservation-{}.attr".format(parent,user["username"])
									print(f"\n        Creating attribute {attr}:\n{port_reservations[parent]}")
									f = open(attr, "w")
									f.write(port_reservations[parent])
									f.close()

								site =  parents_regex.split("-")[0]
								cr_title = f"[DX][MUDA][{site.upper()}] port reservation in {parents_regex}"
								commit_command = "git commit -m '" + cr_title + "'"
								print(bcolors.lightcyan,f"\n        {tool}: git add .",bcolors.end)
								print(bcolors.lightcyan,f"        {tool}: {commit_command}",bcolors.end)
								cr.genevabuilder_git_add_commit(gb_path,commit_command)


								brick_groups = [parents_regex]
								print(f"\n   MUDA format group of devices: {brick_groups}")
								brick_groups_new = []
								for group in brick_groups:
									stem = group.split("r[")[0]
			
									list_devices = mcm.mcm_get_hostnames_from_regex(group)
									list_numbers = []
									for device in list_devices:
										for peer in peers:
											if device in peer:
												list_numbers.append(device.replace(stem,""))
												break
									new_regex = stem + "(" + "|".join(list_numbers) + ")$"
									#print(new_regex)#fra50-br-tra-(r1|r2|r3|r4)$
									brick_groups_new.append(new_regex)
								brick_groups = brick_groups_new
								print(f"   Regex format group of devices: {brick_groups}")
								parents_regex = "|".join(brick_groups)

								#parents_regex = re.findall(method["rwfclidevices"],parents_regex)[0]
								command = '/apollo/env/ReleaseWorkflowCLI/bin/generate_configs.py --devices "{}" --cr --dockets {}'.format(parents_regex,method["dockets"])
								print(bcolors.lightcyan,f"\n        {tool}: {command}",bcolors.end)
								print("        Please wait 20 minutes")
								gb_cr = cr.genevabuilder_generate_configs(gb_path,command)

								if gb_cr:
									print("     Please review and publish your CR, and once it is approved, merge it and run MUDA again:")
									print(bcolors.lightblue,"     https://code.amazon.com/reviews/{}\n".format(gb_cr),bcolors.end)
									merge_command = '/apollo/env/GitLocker/bin/gitlocker.py --devices "{}" --cr {}'.format(parents_regex,gb_cr)
									ddb_table_update(brick['brick'],8,True,gb_cr,merge_command) # waiting_cr_mcm_completion is True

							else:
								print(f"\n        Ports reservation is done in {parents_regex} for {children_regex}.\n        Moving to the next step.")
								ddb_table_update(brick['brick'],10,False)
					else:
						print(f"        Your {tool} repository is not clean. Please clean it before creating a new CR. You can use 'git stash' and 'git clean -d -f' if you don't need the changes.")

				elif "FabricBuilder" in tool:
					print(f"\n        FabricBuilder port reservation is not automated yet. Pending deployment example.")
				elif "Jukebox" in tool:
					print(f"\n        Port reservation in Jukebox will be done in the next step.\n        Moving to the next step.")
					ddb_table_update(brick['brick'],10,False)
				else:
					print(f"        Unknown method {tool}.")


		##########################################################################################
		# 09 == Port Reservation MCM.
		elif int(brick['progress']) == 9:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['gb_port_reservation_mcm'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				if cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						print(f"\n   {last_mcm} is Completed Successful, moving to the next step.")
						ddb_table_update(brick['brick'],10,False)
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")


			#The CR/MCM was not created yet:
			else:
				gb_cr = brick['gb_port_reservation_cr'].split(",")[-1]
				merge_command = brick['merge_command']
				print(f"        Devices BR: {devices_br}\n        Devices Brick: {devices_brick}\n        Devices DX: {devices_dx}\n")


				result = nsm.get_devices_from_nsm(devices_brick[0],state = ['OPERATIONAL','MAINTENANCE'])
				if result == []:
					parents = devices_br
					parents_regex = brick['br']
					children = devices_brick
					children_regex = brick['brick']

				else:

					dx_devices = mcm.mcm_get_hostnames_from_regex(brick['dx'])
					dx_device_list =[]
					for peer in peers:
						for port in peers[peer]['ports']:
							br_device = peer.split('<>')[0]
							br_device_port = port.split(',')[1]
							dx_device = peer.split('<>')[1]

							if re.findall("vc-car|vc-bdr|vc-dar|vc-bar",dx_device) and dx_device in dx_devices and br_device in devices_brick and dx_device not in dx_device_list:
								parse_lower = hercules.get_config_matching_pattern(br_device, 'description .* {}'.format(dx_device.lower()), stream='collected', file_list=['set-config'])
								parse_upper = hercules.get_config_matching_pattern(br_device, 'description .* {}'.format(dx_device.upper()), stream='collected', file_list=['set-config'])
	
								if parse_lower:
									for description in parse_lower:
										if 'interfaces {}'.format(br_device_port) in description:
											dx_device_list.append(dx_device)
											break

								elif parse_upper:
									for description in parse_upper:
										if 'interfaces {}'.format(br_device_port) in description:
											dx_device_list.append(dx_device)
											break

					devices_dx = []
					for peer in peers:
						br_device = peer.split('<>')[0]
						dx_device = peer.split('<>')[1]
						if br_device in devices_brick and dx_device in dx_devices and dx_device not in dx_device_list and dx_device not in devices_dx:
							devices_dx.append(dx_device)
					devices_dx.sort()

					parents = devices_brick
					parents_regex = brick['brick']
					children = devices_dx
					children_regex = muda_auxiliary.regex_from_list(devices_dx)
	

				method = False
				for device_type in muda_data["port_reservation_mcm"]:
					if re.findall(device_type,parents_regex):
						method = muda_data["port_reservation_mcm"][device_type]
						break

				if method:
					print(f"        Ports reservation MCM is required for {parents_regex}.")

					if peers != {}:
						mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("mcm_port_reservation",parents_regex,children_regex,gb_cr)

						if mcm_id:
							print(f"\n        Created {mcm_id}.")
							if method["single_bundle"]:
								bundle_devices = ["/"+parents_regex+"/"]
							else:
								bundle_devices = []
								for device in parents:
									for peer in peers:
										if device in peer.split("<>"):
											bundle_devices.append(device)
											break
							print(f"        Port reservation to be done in: {bundle_devices}")

							list_device = []
							list_generate_command = []
							list_bundle_number = []
							steps = []
							steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
							steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
							for bundle_device in bundle_devices:

								if method["policy_args"]:
									policy_args = method["policy_args"]
									interfaces = []
									lags = []

									for peer in peers:
										if bundle_device in peer:
											port_list = peers[peer]["ports"]
		
											if bundle_device == peer.split("<>")[0]:
												child = peer.split("<>")[1]
												if child in children:
													for port in port_list:
														new_lag = port.split(',')[0]
														if new_lag not in lags:
															lags.append(new_lag)
														interfaces.append(port.split(',')[1])
											else:
												child = peer.split("<>")[0]
												if child in children:
													for port in port_list:
														new_lag = port.split(',')[3]
														if new_lag not in lags:
															lags.append(new_lag)
														interfaces.append(port.split(',')[2])

									if method["check_lag"]:
										config = hercules.get_latest_config_for_device(bundle_device,'collected',['set-config'])
										config = config.decode().replace(' ', '')
										existing_lags = [x for x in lags if re.findall("interfaces{}description".format(x),config)]
										if lags == existing_lags:
											policy_args += " CHECK_LAG_NOT_EXISTS=false"
										else:
											policy_args += " CHECK_LAG_NOT_EXISTS=true"
									if method["interfaces"]:
										str_interfaces = ",".join(interfaces)
										policy_args += f" INTERFACES={str_interfaces}"
									if method["lags"]:
										str_lags = ",".join(lags)
										policy_args += f" LAGS={str_lags}" 

								else:
									policy_args = ""

								generate_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern "{}" --modules {} --stream released --policy {} {} --approvers {}'.format(bundle_device,method["modules"],method["policy"],policy_args,method["approvers"])
								print(f"\n        Creating Alfred Bundle (give it a few minutes). Executing:\n        {generate_command}")

								try:
									output_bytes = subprocess.check_output(generate_command, shell=True)
									output = output_bytes.decode("utf-8")
									bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
									bundle_number = bundle_number.split()[0]

									list_device.append(bundle_device.replace("/",""))
									list_generate_command.append(generate_command)
									list_bundle_number.append(bundle_number)
									print(f"        Bundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")
								except:
									print("        Issue creating the bundle, please create the bundle and update the MCM manually.")
						
							else:
								mcm_overview += "####Bundle Generation:\n"
								for generate_command in list_generate_command:
									mcm_overview += f"```\n{generate_command}\n```\n"
								mcm_overview += "\n####Bundle Diffs/Config/Autochecks:\n"
								for x in range(0,len(list_device)):
									mcm_overview += f"Bundle for {list_device[x]}:  https://hercules.amazon.com/bundle-v2/{list_bundle_number[x]}\n"
								mcm_overview += "\n####Bundle Deployment:\n"
								for x in range(0,len(list_device)):
									mcm_overview += f"Deployment for {list_device[x]}:  /apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {list_bundle_number[x]}\n"
								for x in range(0,len(list_device)):
									steps.append({'title':f'Alfred Bundle Deployment {list_device[x]}','time':300,'description':f'To deploy the bundle:\nhttps://hercules.amazon.com/bundle-v2/{list_bundle_number[x]}\n\nExecute the following:\n/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {list_bundle_number[x]}\n\nTo rollback:\n/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'})
								mcm_overview += "\n####Bundle Dry-Run Result:\n"
								for x in range(0,len(list_device)):
									mcm_overview += f"Dry-Run result for {list_device[x]}: [ENTER_DRYRUN_LINK_HERE]\n"

								print(f"\n        Updating {mcm_id} ...", end = '')
								mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
								print(f" ready, updating MUDA step.")
								print("\n    Please do the Dry-Run of the Bundle before sending the MCM for approvals.")
								print("       For VC-COR changes, use Docket 'DX-Deploy'\n       For BR-TRA changes, use Docket 'IED-BR-TRA'\n       For BR-AGG changes, use Docket 'Regional-Border-Deploy'\n       For BR-KCT, AutoPCN could push the changes, or you can run this MCM if the changes in the DIFF is simple enough, use Docket 'Regional-Border-Deploy'")
								ddb_table_update(brick['brick'],9,True,mcm_id) # waiting_cr_mcm_completion is True
						else:
							print("        Issue creating the MCM.")
					else:
						print("        No information found in the Cutsheets.")
				else:
					print(f"\n        Port reservation MCM is not required.\n        Moving to the next step.")
					ddb_table_update(brick['brick'],10,False)


		##########################################################################################
		# 10 == Conditional manual steps
		elif int(brick['progress']) == 10:
			print("\n    Some deployments require these manual steps. Follow the instructions in MUDA Wiki to complete the task that apply to your deployment:")

			if "-br-agg-" not in devices_brick[0]:
				print("\n    (a) For new PoP: add Joshua Mapping if Site name is different than Region name.")
				print("\n    (b) For new PoP: add the PoP/AZ to Jukebox if you are deploying a new site.")
				print("\n    (c) For new PoP with VC-DAR: update DX Small Edge PoP Template if you have VC-DAR.")

			else:
				print("\n    (a) For new AZ: add the PoP/AZ to Jukebox if you are deploying a new site.")
				print("\n    (b) For new EdgGroup: request BF Pool ID.")
				print("\n    (c) For new EdgGroup: add EdgeGroup to Jukebox.")
				print("\n    (d) Update 100G/10G BR-AGG VC-BAR Jukebox Template.")

			answer = input("\n        All the requirements above are ready or not applicable to your deployment? (y/n)? [n]: ") or "n"
			if answer == "y":
				print("        Moving to the next step.")
				ddb_table_update(brick['brick'],11,False)

		##########################################################################################
		# 11 == Create Jukebox Devices, Cabling and Links.
		elif int(brick['progress']) == 11:

			if brick['dx'] != "None":
				dx_device_not_created = []
				if loopbacks == None:
					print("\n>> ATTENTION: MUDA has been upgraded since the last time that you executed this deployment. To make it work on the new version of MUDA, please run 'new MCM' to re-start your deployment. The re-start would auto-allocate more IP, including BMN management and DNS entries. For more information please reach out to joaq@.")
				else:
					brick_devices = mcm.mcm_get_hostnames_from_regex(brick['brick'])
					dx_devices = mcm.mcm_get_hostnames_from_regex(brick['dx'])


					print("\n>> Checking",bcolors.lightcyan,"DEVICES",bcolors.end,"in Jukebox, for {}.".format(brick['dx']))
					dx_device_not_created = []
					for dx_device in dx_devices:
						try:
							info = jukebox.get_device_detail(dx_device)
							print("   {} is already created in Jukebox.".format(dx_device))
						except:
							print("   {} is NOT created in Jukebox yet.".format(dx_device))
							dx_device_not_created.append(dx_device)

					if dx_device_not_created != []:
						dx_device_not_created.sort()
						dx_devices = muda_auxiliary.regex_from_list(dx_device_not_created).split("|")
						phoenix_groups = [x for x in dx_devices if re.search(r'.*-vc-car-.*-p\d-v\d-r(\[1-2\])',x)]
						single_devices = [x for x in dx_device_not_created if not re.search(r'.*-vc-car-.*-p\d-v\d-r',x)]
						devices_to_create = phoenix_groups + single_devices
						error_creating = False

						vc_edg_to_create = [x for x in devices_to_create if "vc-edg" in x]
						if vc_edg_to_create:
							region = vc_edg_to_create[0][0:3]
							edg_group = region + "_edg_group_1"
							edg_group = input(f"\n>> Enter the EdgGroup (example '{edg_group}'): ") or edg_group

						serial = random.randint(1,100)*100 + 100000
						for device in devices_to_create:
							for device_type in muda_data["jukebox"]:
								if re.findall(device_type,device):
									information = muda_data["jukebox"][device_type]
									design = information["design"]
									mode = information["mode"]
									vendor = information["vendor"]
									model = information["model"]
									os_version = information["os_version"]
									loopback_key = information["loopback"]
									management_key = information["management"]
									realm = muda_auxiliary.get_dx_region(device)
									dns_name = f"{device}.{realm}.amazon.com"
									az = device.split("-")[0]
									device_type = device.split("-")[2]

									print(f"\n>> Adding {design} to Jukebox: "+bcolors.lightcyan+f"{device}"+bcolors.end)
									if mode == "rack":
										device_stem = device.split("-r[")[0]
										pair_number = device.split("-")[-4][-1]
										version = device.split("-")[-3]
										first_router = device_stem+"-r1"
										vccar1 = device_stem + "-r1"
										vccar2 = device_stem + "-r2"

										try:
											ddb.add_device_to_dx_region_table(realm, vccar1)
											ddb.add_device_to_dx_region_table(realm, vccar2)
											bmn_ip = loopbacks[first_router].get("BMNNET")
											bmn_network = str(IPNetwork(bmn_ip + "/27").network) + "/27"

											vccar1_loop = loopbacks[vccar1]["PRIMARYIP_CS"]
											vccar1_loop = str(IPNetwork(vccar1_loop)).replace("/32","")
											vccar2_loop = loopbacks[vccar2]["PRIMARYIP_CS"]
											vccar2_loop = str(IPNetwork(vccar2_loop)).replace("/32","")
											
											rack_sku = loopbacks[first_router].get("SKU")

											print(f"   New rack information to call Jukebox API:\n     Version: {version}\n     SKU: {rack_sku}\n     Pair: {pair_number}\n     Realm: {realm}\n     AZ/PoP: {az}\n     Management: {bmn_network}\n     {vccar1}: {vccar1_loop}\n     {vccar2}: {vccar2_loop}")

											if rack_sku not in  muda_data["jukebox_sku"][version]:
												print("\nERROR: The Version-SKU association is wrong, please re-start your deployment ('new MCM-...') or get get support in Slack 'muda-support'")
												error_creating = True
											else:
												answer = input("\n   Is the information above correct (y/n)? [n]: ") or "n"
												if answer == "y":
													result = jukebox.add_new_rack_to_jb(version, rack_sku, pair_number, realm, az, bmn_network, vccar1_loop, vccar2_loop)
													if not result:
														print(f"\n   ",bcolors.red,"ERROR",bcolors.end,f"Issue creating {design} rack returned by Jukebox API. Please report the issue in Slack #muda-support.")
														error_creating = True
													else:
														print("\n   ATTENTION: after creating the Rack, and while it is not automated by DX Software, you have to manually add Units 50000 and 50001 for the management of both RE. Please click '+1' and follow the instructions in the SIM: https://sim.amazon.com/issues/AWSDXUI-360")
												else:
													print("\n If the information was not correct, please get support in Slack #muda-support.")

										except:
											print(f"\n   ",bcolors.red,"ERROR",bcolors.end,f"Issue creating {design} rack.")
											error_creating = True

									if mode == "rack_telesto":
										brick_num = re.findall('-vc-[a-z]{3}-[a-z]{3}-b([0-9])',device)[0]
										result = None
										
										while result == None:
										
											try:
												device_stem = re.findall('(.*-vc-[a-z]{3}-[a-z]{3}-b[0-9]-r)',device)[0]
												bdr_r1 = device_stem + '1'
												bdr_r2 = device_stem + '2'
												bdr_r3 = device_stem + '3'
												bdr_r4 = device_stem + '4'
												ddb.add_device_to_dx_region_table(realm, bdr_r1)
												ddb.add_device_to_dx_region_table(realm, bdr_r2)
												ddb.add_device_to_dx_region_table(realm, bdr_r3)
												ddb.add_device_to_dx_region_table(realm, bdr_r4)
												bmn_ip = loopbacks[device].get("BMNNET")
												bmn_network = str(IPNetwork(bmn_ip + "/27").network) + "/27"
												loopbacks_subnet = '198.18.254.0/27'
												brick_subnet = loopbacks[device].get("BrickAggregate")
												shard_subnet = loopbacks[device].get("ShardAggregate")
												
												
												
												print(f"   Follow the steps below to create ew rack information in Jukebox:\n     Open the link 'https://jukebox-web.corp.amazon.com/#/editDX20Rack/new' on the web browser\n     Enter the following information on the webpage\n     REALM: {realm}\n     AZ: {az}\n     BRICK NUMBER: {brick_num}\n     BMN IP ADDRESS SUBNET (/27): {bmn_network}\n     LOOPBACK IP ADDRESS SUBNET (/27): {loopbacks_subnet}\n     BRICK AGGREGATE SUBNET (/26): {brick_subnet}\n     SHARD AGGREGATE SUBNET (/29): {shard_subnet}\n")
												
												
												answer = input("\n   Telesto Rack has been created via JB GUI (y/n)? [n]: ") or "n"
												if answer == "y":
													result = jukebox.get_device_detail(device)
													if not result:
														print(f"\n   ",bcolors.red,"ERROR",bcolors.end,f"{design} rack was not found in Jukebox. Please report the issue in Slack #muda-support if rack was created and error exists.")
														error_creating = True
												else:
													print("\n If the information was not correct, please get support in Slack #muda-support.")
											
											except:
												print(f"\n   ",bcolors.red,"ERROR",bcolors.end,f"{design} rack was not found in Jukebox. Please report the issue in Slack #muda-support if rack was created and error exists.")
												error_creating = True

									elif mode == "single":

										serial += 1
										try:
											loopback = str(IPNetwork(loopbacks[device][loopback_key])[0])
											management = str(IPNetwork(loopbacks[device][management_key])[0])
										except:
											print(f"\n   ",bcolors.red,"ERROR",bcolors.end,f"Management IP or Loopbacks for {device_type.upper()} missing.")
											error_creating = True

										else:
											if re.findall("-vc-dar-",device):
												coral_device = CoralDevice(
													hostname=device,dns_name=dns_name,device_state="planned",
													realm=realm,az=az,device_type=device_type,
													manufacturer=vendor,model=model,serial=str(serial),os_version=os_version,
													loopback_addresses=[{"ipv4Address":loopback,"ipv6_address":"::","unitNumber":0,"pathColor":"gray"}],
													management_address=management,
													sostenuto_addresses=[],)
											elif re.findall("-vc-bar-",device):
												coral_device = CoralDevice(
													hostname=device,dns_name=dns_name,device_state="planned",
													realm=realm,az=az,device_type=device_type,
													manufacturer=vendor,model=model,serial=str(serial),os_version=os_version,
													loopback_addresses=[{"ipv4Address":loopback,"unitNumber":0,"pathColor":"gray"}],
													management_address=management,
													sostenuto_addresses=[],)
											elif re.findall("-vc-edg-",device):
												coral_device = CoralDevice(
													hostname=device,dns_name=dns_name,device_state="planned",
													realm=realm,az=az,device_type=device_type,
													manufacturer=vendor,model=model,serial=str(serial),os_version=os_version,
													loopback_addresses=[{"ipv4Address":loopback,"unitNumber":0,"pathColor":"gray"}],
													management_address=management,
													south_interface_mac_address="00:00:6c:12:34:56",
													edg_group=edg_group,
													sostenuto_addresses=[],)

											print(f"   Creating device:\n{coral_device}")

											try:
												ddb.add_device_to_dx_region_table(realm, device)
												result = jukebox.add_new_device_to_jb(coral_device,[],[],az)
											except Exception as e:
												print(f"\n   ERROR: creating device in Jukebox:\n   {e}")
												error_creating = True

											else:
												print("   Device created, please review and submit the edit (https://jukebox-web.corp.amazon.com/#/pendingEdits)")

						if error_creating:
							print("\n MUDA couldn't create the devices, plese fix the issues or get support on Slack Channel #muda-support.\n")
						else:
							print("\n Once the Device creations are approved in Jukebox, run MUDA again and it will add the ports between devices.\n")

					else:
						
						any_device_edited = False
						for device_a in dx_devices:
							print("\n>> Checking",bcolors.lightcyan,"CABLING/LINKS",bcolors.end,"in Jukebox for",bcolors.lightcyan,f"{device_a}",bcolors.end,".")
							this_device_edited = False
							this_device_error = False
							info = jukebox.get_device_detail(device_a)
							links_info = info.data.links
							cabling_info = info.data.cabling

							#print(f"\nInitial Links Info:\n{links_info}")
							#print(f"\nInitial Cabling Info:\n{cabling_info}\n")

							for peer in peers:
								if device_a in peer.split("<>"):

									if device_a == peer.split("<>")[0]:
										device_z = peer.split("<>")[1]
										ports = peers[peer]["ports"]
									elif device_a == peer.split("<>")[1]:
										device_z = peer.split("<>")[0]
										ports = peers[peer]["ports"]
										ports = [",".join(x.split(",")[::-1]) for x in ports]#flipping ports

									print(f"   PEER {device_a}<>{device_z}")

									for port in ports:
										port_a = port.split(",")[1]
										port_z = port.split(",")[2]
										print(f"     Cabling {port_a} to {port_z} ... ", end="")

										for cabling in cabling_info:
											#print(cabling)
											if ((cabling.device_a_name == device_a) and (cabling.device_a_interface_name == port_a) and (cabling.device_z_name == device_z) and (cabling.device_z_interface_name == port_z)) or ((cabling.device_a_name == device_z) and (cabling.device_a_interface_name == port_z) and (cabling.device_z_name == device_a) and (cabling.device_z_interface_name == port_a)):
												print("found in JB.")
												break
										else:
											print("NOT found, adding to JB.")
											this_device_edited = True
											any_device_edited = True
											info.data.cabling.append(DeviceCabling(device_a_name=device_a, device_a_interface_name=port_a, device_z_name=device_z, device_z_interface_name=port_z))

									print("     Link IP information ... ", end="")
									for link in links_info:
										if ((link.device_a_name == device_a) and (link.device_z_name == device_z)) or ((link.device_a_name == device_z) and (link.device_z_name == device_a)):
											print("found in JB.")
											try:#If expected/existing, it adds the IPv6 to Peers
												ipv6_key = [x for x in peers[peer] if re.findall(r"^ipv6.*",x)][0]
												peers[peer][ipv6_key] = link.inet6_link_cidr
												print("     Added IPv6 information from Jukebox to MUDA Database.")
											except:
												pass
											break
									else:
										inet_key = [x for x in peers[peer] if re.findall(r"^inet.*",x)]
										csc_key = [x for x in peers[peer] if re.findall(r"^csc.*",x)]
										p2p_key = [x for x in peers[peer] if re.findall(r"^p2p.*",x)]
										ipv6_key = [x for x in peers[peer] if re.findall(r"^ipv6.*",x)]
										ec2_key = [x for x in peers[peer] if re.findall(r"^ec2.*",x)]

										if inet_key or csc_key or p2p_key or ipv6_key or ec2_key:
											print("NOT found, ", end="")
											this_device_edited = True
											any_device_edited = True
										else:
											print("nothing to add.")

										link_type = ""
										for device_type in muda_data["jukebox"]:
											if re.findall(device_type,device_a):
												link_types = muda_data["jukebox"][device_type]["link_types"]
												for pattern in link_types:
													if re.findall(pattern,device_z):
														link_type = link_types[pattern]

										if inet_key and csc_key and ipv6_key:
											try:
												inet_ip = str(IPNetwork(peers[peer][inet_key[0]]))
												csc_ip = str(IPNetwork(peers[peer][csc_key[0]]))
												ipv6_ip = "::/127"
												print(f"adding INET {inet_ip}, CSC {csc_ip}, IPV6 {ipv6_ip} TYPE {link_type}")
												info.data.links.append(DeviceLink(device_a_name=device_a, device_z_name=device_z, link_cidr=inet_ip, inet6_link_cidr=ipv6_ip, csc_link_cidr=csc_ip, link_type=link_type))
											except:
												print(f"ERROR missing IP information.")
												this_device_error = True

										elif inet_key and csc_key and not ipv6_key:
											try:
												inet_ip = str(IPNetwork(peers[peer][inet_key[0]]))
												csc_ip = str(IPNetwork(peers[peer][csc_key[0]]))
												print(f"adding INET {inet_ip}, CSC {csc_ip} TYPE {link_type}")
												info.data.links.append(DeviceLink(device_a_name=device_a, device_z_name=device_z, link_cidr=inet_ip, csc_link_cidr=csc_ip, link_type=link_type))
											except:
												print(f"ERROR missing IP information.")
												this_device_error = True

										elif inet_key and not csc_key and not ipv6_key:
											try:
												inet_ip = str(IPNetwork(peers[peer][inet_key[0]]))
												print(f"adding INET {inet_ip} TYPE {link_type}")
												info.data.links.append(DeviceLink(device_a_name=device_a, device_z_name=device_z, link_cidr=inet_ip, link_type=link_type))
											except:
												print(f"ERROR missing IP information.")
												this_device_error = True
										elif inet_key and ipv6_key and not csc_key:
											try:
												inet_ip = str(IPNetwork(peers[peer][inet_key[0]]))
												ipv6_ip = "::/127"
												print(f"adding INET {inet_ip} TYPE {link_type}, IPV6 {ipv6_ip} TYPE {link_type}")
												info.data.links.append(DeviceLink(device_a_name=device_a, device_z_name=device_z, link_cidr=inet_ip, inet6_link_cidr=ipv6_ip,link_type=link_type))
											except:
												print(f"ERROR missing IP information.")
												this_device_error = True
										
										elif ec2_key:
											try:
												ec2_ip = str(IPNetwork(peers[peer][ec2_key[0]]))
												print(f"adding EC2 {ec2_ip} TYPE {link_type}")
												info.data.links.append(DeviceLink(device_a_name=device_a, device_z_name=device_z, link_cidr=ec2_ip, link_type=link_type))
											except:
												print(f"ERROR missing IP information.")
												this_device_error = True

							if this_device_edited and not this_device_error:
								print(f"   UPDATING Jukebox for {device_a}")
								#print(f"\nNew Links Info:\n{links_info}")
								#print(f"\nNew Cabling Info:\n{cabling_info}\n")
								try:
									jukebox.edit_full_device(device_a,info.data.cabling,info.data.links)
								except Exception as e:
									print(bcolors.red+f"     Error editing {device_a}: {e}"+bcolors.end)
							elif this_device_error:
								print(f"   No changes for {device_a} due to",bcolors.red,"ERROR",bcolors.end,"missing IP information.")
							else:
								print(f"   No changes for {device_a}")
											
						if any_device_edited:

							if [x for x in dx_devices if "-vc-edg-" in x]:#If VC-EDG devices are modifyied, manually add WoodChipper Port Reservation.
								print("\n   On the VC-EDG you have to manually add the ",bcolors.lightcyan,"WoodChipper Port Reservations:",bcolors.end)
								print("   For each VC-EDG, edit again the JB pending changes, in the 'Port Reservation' section add 'xe-0/2/1' and 'xe-/1/2/1', with reason 'woodchipper' and Type 'Woodchipper'.")
								print("   More information in https://w.amazon.com/bin/view/Interconnect/Deployment_Team/edge_scaling#HNote:WoodChipperPortReservations:WoodChipper28WX29requirestwoportsoneachVC-EDGtobereservedforGREtunnelcreation.")

							answer = input("\n   Press Enter when that is done...")

							print("\n   Please check",bcolors.lightcyan,"https://jukebox-web.corp.amazon.com/#/pendingEdits",bcolors.end,"and if the changes are good, submit them and get approvals.\n   Then run MUDA again.")#Not using Step 6 anymore.

						else:
							print("\n   Devices, Cabling and Links are ready in Jukebox.")
							print(f"\n   Checking NSM status for {brick['dx']}.")
							for device in dx_devices:
								result = nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
								if device not in result:
									print(f"     The device {device} is NOT Operational in NSM, so we are doing a Deployment (not Backhaul Scaling), moving to Step (15).")
									ddb_table_update(brick['brick'],15,False,peers,loopbacks)#Updating Peers and Loopbacks since added IPv6
									break
							else:
								print(f"     All the DX Devices are Operational in NSM, we could require Port Reservation MCM for {brick['dx']}, moving to the next step.")
								ddb_table_update(brick['brick'],12,False,peers,loopbacks)#Updating Peers and Loopbacks since added IPv6

			else:
				print("     There are no DX devices, moving to Step (16).")
				ddb_table_update(brick['brick'],16,False,peers,loopbacks)#Updating Peers and Loopbacks since added IPv6


		##########################################################################################
		# 12 == DX Devices Port Reservation MCM
		elif int(brick['progress']) == 12:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['dx_port_reservation_mcm'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				if cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						print(f"\n   {last_mcm} is Completed Successful, moving to the next step.")
						ddb_table_update(brick['brick'],13,False)
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")

			#The CR/MCM was not created yet:
			else:
				last_cutsheet = brick.get('cutsheet_mcm').split(",")[-1]
				brick_devices = mcm.mcm_get_hostnames_from_regex(brick['brick'])
				dx_devices = mcm.mcm_get_hostnames_from_regex(brick['dx'])

				print(f"\n   Checking NSM status for {brick['dx']}.")
				operational_devices = []
				for device in dx_devices:
					operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])

				op_devices = [x for x in dx_devices if x in operational_devices]

				print(f"\n   The following devices are Operational in NSM, so they could require Port Reservation MCM:\n     {op_devices}")

				new_dx_ports = {}
				for device in op_devices:
					directory = "{}/MUDA/Alfred/{}".format(user["muda_path"],device)
					if not os.path.exists(directory):
						os.makedirs(directory)
					file_conf = directory + "/{}.conf".format(device)
					file_args = directory + "/{}.args".format(device)

					f = open(file_conf, "w")
					f.write("interfaces {\n")
					device_ports = []

					config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
					if config != None:
						config = config.decode().replace(' ', '')
						print(f"\n>> Checking ports on {device}:")
						for peer in peers:
							if re.findall(device,peer):
								if device == peer.split("<>")[0]:
									device_z = peer.split("<>")[1]
									ports = peers[peer]["ports"]
								elif device == peer.split("<>")[1]:
									device_z = peer.split("<>")[0]
									ports = peers[peer]["ports"]
									ports = [",".join(x.split(",")[::-1]) for x in ports]#flipping ports
								for port in ports:
									port_a = port.split(",")[1]
									port_z = port.split(",")[2]
									print(f"     Port {port_a} to {device_z} ... ", end="")
									pattern = f"interfaces{port_a}description\"{device_z}"

									if re.findall(pattern,config):
										print(f"valid.")
									else:
										print(f"NOT found.")
										f.write('    replace: {} {{\n'.format(port_a))
										f.write('        description "TURNUP--> {} {} {}";\n'.format(port_z,device_z,last_cutsheet))
										f.write('        unit 0;\n')
										f.write('        }\n')
										device_ports.append(port_a)

										if device not in new_dx_ports:
											new_dx_ports[device] = []
										new_dx_ports[device].append(port_a)

					f.write('}\n')
					f.write('protocols {\n')
					f.write('    lldp {\n')
					for port in device_ports:
						f.write('    interface {};\n'.format(port))
					f.write('    }\n')
					f.write('}\n')
					f.close()

					f = open(file_args, "w")
					f.write("""CHECK_ALL_ALARMS=true
CHECK_DESCRIPTION_REGEX=true
CHECK_INTERFACES_NOT_IN_LAG=true
CHECK_INTERFACE_STATE=false
CHECK_LAG_NOT_EXISTS=false
CHECK_LAG_STATE=false
CHECK_TRAFFIC=false
IGNORE_ALARMS=false
REGEXSTRING=TURNUP
UPDATE_PROVISIONING=true
INTERFACES={}""".format(','.join(device_ports)))
					f.close()


				if new_dx_ports:
					vccar_regex = list(new_dx_ports.keys())
					vccar_regex.sort()
					vccar_regex = muda_auxiliary.regex_from_list(vccar_regex)
					print(f"\n>> MCM creation.")
					mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("vccar_vccor_port_reservation",vccar_regex,brick['brick'],last_cutsheet)
					if mcm_id:
						print(f"   Created {mcm_id}.")

						list_device = []
						list_generate_command = []
						list_bundle_number = []
						steps = []
						steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
						steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
						for device in new_dx_ports:
							directory = "{}/MUDA/Alfred/{}".format(user["muda_path"],device)
							file_conf = directory + "/{}.conf".format(device)
							file_args = directory + "/{}.args".format(device)
							print(f"\n   VAR files created for Port Reservation on {device}:\n     {file_conf}\n     {file_args}")

							try:
								pwd = os.getcwd()
								command = "cp {} {}".format(file_conf,pwd+"/"+device+".conf")
								executed = subprocess.check_output(command, shell=True)
								command = "cp {} {}".format(file_args,pwd+"/"+device+".args")
								executed = subprocess.check_output(command, shell=True)
							
								generate_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --devices {} --policy vc_reserve_interfaces.yaml --policy-args-file {}.args --local-files {}.conf --approvers l1-approver'.format(device,device,device)
								print(f"   BUNDLE creation command:\n     {generate_command}")
							
								#output_bytes = subprocess.check_output(generate_command, shell=True)
								#output = output_bytes.decode("utf-8")

								output_bytes = subprocess.run(generate_command, shell=True,stdout=PIPE, stderr=STDOUT)
								output = output_bytes.stdout.decode()

								bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
								bundle_number = bundle_number.split()[0]

								list_device.append(device)
								list_generate_command.append(generate_command)
								list_bundle_number.append(bundle_number)
								print(f"     Bundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")

								command = "rm {}".format(pwd+"/"+device+".conf")
								executed = subprocess.check_output(command, shell=True)
								command = "rm {}".format(pwd+"/"+device+".args")
								executed = subprocess.check_output(command, shell=True)

							except Exception as e:
								print("\nError creating the Bundle for {}: {}\n".format(device,e))
								break

						else:
							mcm_overview += "####Bundle Generation:\n"
							for generate_command in list_generate_command:
								mcm_overview += f"```\n{generate_command}\n```\n"
							mcm_overview += "\n####Bundle Diffs/Config/Autochecks:\n"
							for x in range(0,len(list_device)):
								mcm_overview += f"Bundle for {list_device[x]}:  https://hercules.amazon.com/bundle-v2/{list_bundle_number[x]}\n"
							mcm_overview += "\n####Bundle Deployment:\n"
							for x in range(0,len(list_device)):
								mcm_overview += f"Deployment for {list_device[x]}:  /apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {list_bundle_number[x]}\n"
							for x in range(0,len(list_device)):
								steps.append({'title':f'Alfred Bundle Deployment {list_device[x]}','time':300,'description':f'To deploy the bundle:\nhttps://hercules.amazon.com/bundle-v2/{list_bundle_number[x]}\n\nExecute the following:\n/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {list_bundle_number[x]}\n\nTo rollback:\n/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'})
							mcm_overview += "\n####Bundle Dry-Run Result:\n"
							for x in range(0,len(list_device)):
								mcm_overview += f"Dry-Run result for {list_device[x]}: [ENTER_DRYRUN_LINK_HERE]\n"

							print(f"\n        Updating {mcm_id} ...", end = '')
							mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
							print(f" ready, updating step.")
							print("\n    Please do the Dry-Run of the Bundle before sending the MCM for approvals.\n")
							ddb_table_update(brick['brick'],12,True,mcm_id,new_dx_ports)

							print(f"\n>> Note: the following ports will be turned DOWN after Mobius test.")
							for device in new_dx_ports:
								print(f"   {device}: {new_dx_ports[device]}")
								#new_dx_ports = { Save this variable in DynamoDB for the future step
								#	"iad53-vc-car-r1": ["xe-0/0/1","xe-2/3/1"],
								#	"iad53-vc-car-r2": ["xe-0/0/4","xe-2/3/4"]
								#	}

					else:
						print("        Issue creating the MCM.")
				else:
					print("\n>> No port reservation needed, no Backhaul Scaling project detected, and devices already in-service.")
					print("   Deployment completed moving to the last step.")
					ddb_table_update(brick['brick'],38,False)


		##########################################################################################
		# 13 == Scaling port testing with Mobius
		elif int(brick['progress']) == 13:

			ports_to_shutdown = brick['ports_to_shutdown']
			print("        Complete Mobius test using https://w.amazon.com/bin/view/DXDEPLOY_Automation_Others/Scripts/dx_mobius.py/")
			for device in ports_to_shutdown:
				print(f"   {device}: {ports_to_shutdown[device]}")
			answer = input("\n>> Do you want to move to the next step (y/n)? [n]: ") or "n"
			if answer == "y":
				ddb_table_update(brick['brick'],14,False)


		##########################################################################################
		# 14 == Scaling Create port shutdown MCM
		elif int(brick['progress']) == 14:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['port_shutdown_mcm'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				if cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						print(f"\n   {last_mcm} is Completed Successful.")
						print(bcolors.lightcyan,f"\n   ACLMANAGE MCM:",bcolors.end,"\n       If your Scaling adds new LAGs, you need ACLManage MCM. Use the script 'acl_manage_mcm.py' manually for that.\n       If your Scaling only adds Links, you don't need ACLManage MCM.")

						answer = input(f"\n>> Did you complete the ACLManage MCM if needed? [n]: ") or "n"
						if answer == "y":
							print("   Moving to the next Step.")
							ddb_table_update(brick['brick'],16,False,peers,loopbacks)
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")


			#The CR/MCM was not created yet:
			else:
				ports_to_shutdown = brick['ports_to_shutdown']
				print("\n>> Create MCM to shutdown the ports:.")
				for device in ports_to_shutdown:
					print(f"   {device}: {ports_to_shutdown[device]}")

				print("\nUse the following Wiki for scaling and create the MCM to shutdown the ports:\nhttps://w.amazon.com/bin/view/DXDEPLOY/Runbooks/VC-CAR_NR_Layer_Scaling_Procedure/#HStep-7:AdmindownportsincutsheetonVC-CARdevices:")

				mcm_id = input("\n>> Enter the MCM to shutdown the ports [MCM-00000000]: ") or "n"
				if re.findall("^MCM-[0-9]+$",mcm_id):
					ddb_table_update(brick['brick'],14,True,mcm_id)


		##########################################################################################
		# 15 == ACLManage MCM before BGP Prestage
		elif int(brick['progress']) == 15:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['mcm_aclmanage'].split(",")[-1]
				if check_mcm_completed_successful(last_mcm,modeledcm):
					ddb_table_update(brick['brick'],16,False,peers,loopbacks)

			#The CR/MCM was not created yet:
			else:
				bgp_prestaged = False
				brick_operational = True #This variable only matters in step (23) for new VC-COR deployments
				required_mcm,mcm_id = create_aclmanage_mcm(peers,loopbacks,devices_br,devices_brick,devices_dx,bgp_prestaged,brick_operational)
				if mcm_id:
					print(f"\n>> Created {mcm_id}. Updating MUDA step.")
					ddb_table_update(brick['brick'],15,True,mcm_id)
				elif not required_mcm:
					print("\n>> ACLManage MCM not required at this time. Moving to the next Step.")
					ddb_table_update(brick['brick'],16,False,peers,loopbacks)
				else:
					print("\n>> Issue creating MCM.")


		##########################################################################################
		# 16 == Ready to create GenevaBuilder attribute CR for Brick and Tiedown.
		elif int(brick['progress']) == 16:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				gb_cr = brick['gb_cr'].split(",")[-1]
				merge_command = brick['merge_command']
				gb_path = user["gb_path"]
				print("\n        MUDA checks if the CR is merged in your local GB repo, so make sure that your GB repo is updated after the merge.")
				if cr.cr_status_closed(gb_path,gb_cr):
					print(f"        The {gb_cr} is already merged. Checking Operational status of Brick devices.")
					operational_devices = []
					for device in devices_brick:
						operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
					op_devices = [x for x in devices_brick if x in operational_devices]
				
					if devices_brick == op_devices:
						print(f"        All the Brick devices are operational. Moving to Step (22)")
						ddb_table_update(brick['brick'],22,False)
					else:
						print(f"        The Brick devices are NOT operational. Please use the following command to release Border configs:")
						release_command = brick['release_command']
						print(bcolors.lightblue,f"     {release_command}",bcolors.end)

						answer = input("\n   Press Enter when that is done...")
						print("\n   Moving to the next step.")
						ddb_table_update(brick['brick'],17,False)

				else:
					print(f"        The {gb_cr} is not merged yet.")
					print("        When it is approved, use the following command to merge:")
					print(bcolors.lightblue,f"     {merge_command}",bcolors.end)
					

			#The CR/MCM was not created yet:
			else:
				print(f"        Devices BR: {devices_br}\n        Devices Brick: {devices_brick}\n        Devices DX: {devices_dx}\n")

				port_reservation_nde = brick.get('port_reservation_nde')
				method = None
				for brick_type in muda_data["gb_attributes_cr"]:
					if re.findall(brick_type,brick['brick']):
						method = muda_data["gb_attributes_cr"][brick_type]
						tool = method["tool"]
						break

				if method and peers!={}:
					created_files = {}

					print(f"\n>> Attribute creation for {brick['brick']} in {tool}.")
					if "GenevaBuilder" in tool:
						gb_path = os.path.expanduser("~")+"/"+tool
						print(bcolors.lightcyan,f"\n        {tool}: git status",bcolors.end)
						if cr.genevabuilder_git_status_ready(gb_path):
							print(f"        Your {tool} repository is clean.")
							print(bcolors.lightcyan,f"        {tool}: git pull --rebase",bcolors.end)
							cr.genevabuilder_git_pull(gb_path)
							print(f"\n        Your {tool} repository is updated now.")
						
							remove_port_reservation = True
							create_kct_lagmembers = False
							attr_modified = muda_genevabuilder.create_attributes(devices_brick,brick_type,peers,loopbacks,created_files,df,port_reservation_nde,remove_port_reservation,create_kct_lagmembers)
						
							attr_tiedown =  False
							tiedown = tiedown_get(devices_brick,peers,loopbacks)
							tiedown = tiedown_missing(tiedown)

							operational_devices = []
							for device in devices_brick:
								operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
							op_devices = [x for x in devices_brick if x in operational_devices]

							if tiedown != {} and devices_brick != op_devices:
								created_files = {}
								created_files = tiedown_create(tiedown,created_files)
								#print(created_files)
								if created_files:
									brick_groups = geneva_builder_append(created_files)
									if brick_groups:
										attr_tiedown = True

							if attr_modified:
								if attr_tiedown:
									print("\n>> Create GB CR for changes in Brick {} and Tiedown.".format(brick['brick']))
									brick_groups.append(brick['brick'])
								else:
									print("\n>> Create GB CR for changes in Brick {}.".format(brick['brick']))
									brick_groups = [brick['brick']]
								create_cr(brick_groups,peers,[],gb_path,tiedown,16)#Next step is (16,True)
								
								if "-vc-cor-" in brick['brick']:
									print(bcolors.lightcyan,"\n>> WARNING: MUDA has created a default 'chassis_port_speeds.attr' for MX10K, which covers most DX Downlink scenarios. Please review this file carefully and if it doesn't work for your deployment, fix it in a second revision of the CR.\n",bcolors.end)

							else:
								print("\n>> No GB changes in Brick {}".format(brick['brick']))
								print(f"   Checking NSM status for {brick['brick']}.")
								operational_devices = []
								for device in devices_brick:
									operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
								op_devices = [x for x in devices_brick if x in operational_devices]
								if devices_brick == op_devices:
									print(f"   All the Brick devices are operational. Moving to Step (22)")
									ddb_table_update(brick['brick'],22,False)
								else:
									print(f"   Not all the devices are operational. Moving to the next step.")
									ddb_table_update(brick['brick'],17,False)

						else:
							print(f"        Your GB repository {gb_path} is not clean. Please clean it before creating a new CR. You can use 'git stash' and 'git clean -d -f' if you don't need the changes.")

				else:
					print(f"        Not method found for your deployment on this Step.")


		##########################################################################################
		# 17 == Waiting for Border release and prestage with AutoPCN/ManualPCN
		elif int(brick['progress']) == 17:

			#Waiting for prestage:
			if waiting_cr_mcm_completion:
				stream = 'collected'#Polled by Hercules daily
				stream_text = "prestage"
			#Waiting for release:
			else:
				stream = 'released'
				stream_text = "release"

			next_progress = int(brick['progress']) + 1

			vccor = mcm.mcm_get_hostnames_from_regex(brick['brick'])[0]
			config = hercules.get_latest_config_for_device(vccor, stream='released')#Brick is always only released at this point.

			if config != None:
				config = config.decode().replace(' ', '')
				border_prestage = []
				border_prestage_ready = []
				border_prestage_pending = []
				for device,b in re.findall(r'description"({}-(br|en)-[a-z0-9-]*)"'.format(vccor.split("-")[0]),config):
					border_prestage.append(device)
				for device,b in re.findall(r'description"({}-(vc)-cor[a-z0-9-]*)"'.format(vccor.split("-")[0]),config):
					if device not in devices_brick:#adding other VC-CORs in the same TC but not the ones for this Brick
						border_prestage.append(device)

				border_prestage = list(dict.fromkeys(border_prestage))
				print(f"\n        List of Border iBGP peers: {border_prestage}\n")

				with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
					future_to_border = {executor.submit(check_border_device_ready, stream, device, vccor): device for device in border_prestage}
					for future in concurrent.futures.as_completed(future_to_border):
						info = future_to_border[future]
						try:
							if future.result() == 0:
								print(f"        Checking {info} ... {stream_text} NOT ready.")
								border_prestage_pending.append(info)
							elif future.result() == 1:
								print(f"        Checking {info} ... {stream_text} OK.")
								border_prestage_ready.append(info)
							elif future.result() == 2:
								print(f"        Checking {info} ... {stream_text} ignored, not Operational.")
								border_prestage_ready.append(info)
							else:
								print(f"        Checking {info} ... {stream_text} pending, NSM retrieve failed.")
								border_prestage_pending.append(info)

						except Exception as e:
							print(f"Error: {e}")

				if border_prestage_pending == []:
					if stream_text == "release":
						print(f"\n        All Border Layers configurations are {stream} for {brick['brick']}, updating MUDA step")
						ddb_table_update(brick['brick'],17,True)
					else:
						print(f"\n        All Border Layers configurations are {stream} for {brick['brick']}.")

						print("\n        MUDA will now do a second validation of BGP/RSVP prestaged completion, with the data from website:")
						print("        https://dxdeploymenttools.corp.amazon.com/vccor/border_bgp_rsvp_status")

						bgp_rsvp_table = ddb.get_ddb_table('vc_cor_bgp_rsvp_prestage_table')
						bgp_rsvp_dict = ddb.scan_full_table(bgp_rsvp_table)
						all_good = True
						for device in devices_brick:
							for device_checked in bgp_rsvp_dict:
								if device == device_checked["Name"]:
									bgp_prestaged = device_checked["bgp_fully_prestaged"]
									rsvp_prestaged = device_checked["rsvp_fully_prestaged"]
									print(f"        Checking {device} prestage completion: BGP {bgp_prestaged}, RSVP {rsvp_prestaged}")
									if bgp_prestaged != "yes" or rsvp_prestaged != "yes":
										all_good = False

						if all_good:
							print(f"\n   Moving to the next step.")
							ddb_table_update(brick['brick'],18,False)
						else:
							print("\n        The website 'border_bgp_rspv_status' gets updated each 6h, so you can wait or investigate why some prestage is missing.")

				else:
					if stream == "released":
						print(f"\n        Border devices pending release: {border_prestage_pending}.\n        Please release the configurations as indicated in the previous step.")
					elif stream == "collected":
						print(f"\n        Border devices pending prestage: {border_prestage_pending}.")

						print("\n        Border layers",bcolors.cyan,"EN-TRA/GCT, BR-TRA/BIB/UBQ/DCR/LLE/SBC have AutoPCN",bcolors.end,"so give them one/two weeks and it will be prestage automatically.")
						print("           If AutoPCN fails, troubleshoot the cause using: https://w.amazon.com/bin/view/VC-COR_prestage_on_IEE_devices/")
						print("           Then, reach out to the Border team owner to fix AutoPCN: IEE owns BR-TRA/BIB/UBQ and EN-TRA/GCT; RBE owns BR-DCR/LLE/SBC; BB owns BR-COR/RRR")
						print("           If you can't wait for the fix, MUDA can create ManualPCN MCMs to unblock your deployment.")
						print("        Border layers",bcolors.cyan,"BR-COR/RRR do not have AutoPCN",bcolors.end,"and MUDA can create ManualPCN MCMs for them.")
						print("        Other",bcolors.cyan,"VC-COR bricks in the same TC do not have AutoPCN/ManualPCN",bcolors.end,"and MUDA does not create any MCM for them.")
						print("           Prestaging other VC-COR bricks in the TC is a manual process, waiting for VC-COR onboarding on PCN.")
						print("           This is the single example MCM so far: https://mcm.amazon.com/cms/MCM-38201993")
						print("        The",bcolors.cyan,"Tiedown requires Alfred MCM",bcolors.end,"and MUDA can create it automatically.\n")
						

						mcm_id_list = []
						br_site = border_prestage_pending[0].split("-")[0]
						answer = input("        Do you want to create ManualPCN/Alfred MCMs? (y/n)? [n]: ") or "n"
						if answer == "y":

							if brick.get('tiedown'):#This means that the CR at step (16) created a tiedown, so check if we have to prestage it or not
								tiedown = brick['tiedown']
								#tiedown = {'iah50': {'br-cor': ['iah50-br-cor-r1', 'iah50-br-cor-r2', 'iah50-br-cor-r3', 'iah50-br-cor-r4'], 'prefixes': ['150.222.223.0/24'], 'shared': 'static-iah50-tiedown.attr'}}
								#br_cor = nsm.get_devices_from_nsm(f"{br_site}-br-cor",state = ['OPERATIONAL','MAINTENANCE'])

								for tc in tiedown:
									tc_upper = tc.upper()
									brcor_regex = muda_auxiliary.regex_from_list(tiedown[tc]['br-cor'])
									config = hercules.get_latest_config_for_device(tiedown[tc]['br-cor'][0],"collected",['set-config'])
									if config != None:
										config = config.decode().replace(' ', '')
										prefix_to_tiedown = []
										for prefix in tiedown[tc]['prefixes']:
											if not re.findall(r'staticroute{}'.format(prefix),config):
												prefix_to_tiedown.append(prefix)

										if prefix_to_tiedown != []:
											list_of_prefixes = ",".join(prefix_to_tiedown)
											print(bcolors.cyan,f"\n     >> TIEDOWN {tc_upper}:",bcolors.end,f"required Afred MCM Tiedown on {brcor_regex} for {list_of_prefixes}. Do you want to create it ", end = '')
											answer = input("(y/n)? [n]: ") or "n"
											if answer == "y":
												supernet = str(IPNetwork(prefix_to_tiedown[0]).supernet(16)[0])
												var_file = create_var_file_tiedown(tc,list_of_prefixes,supernet)
												if var_file:
													mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("brcor_tiedown_prestage",brcor_regex,list_of_prefixes,brick['gb_cr'])
													if mcm_id:
														print(f"        Created {mcm_id}.")
														mcm_id_list.append(mcm_id)

														generate_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern /"{}-br-cor-r.*"/ --modules staticroute --policy tiedown-cor.yaml --stream released --policy-args-file {} --approvers neteng-is-dply-l1-approver --show-rendered-config-diff'.format(tc,var_file)
														print(f"        Creating Alfred Bundle, please wait 5 minutes. Executing command:\n           {generate_command}")
												
														try:
															output_bytes = subprocess.check_output(generate_command, shell=True)
															output = output_bytes.decode("utf-8")
															bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
															bundle_number = bundle_number.split()[0]

															print(f"        Bundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")

															mcm_overview += f"####Bundle Generation:\n{generate_command}\n"
															mcm_overview += f"\n####Bundle Diffs/Config/Autochecks:\nhttps://hercules.amazon.com/bundle-v2/{bundle_number}\n"
															mcm_overview += f"\n####Bundle Deployment:\n/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_number}\n"
															mcm_overview += "\n####Bundle Dry-Run Result:\n[ENTER_DRYRUN_LINK_HERE]\n"

															steps = []
															steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
															steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
															steps.append({'title':'Alfred Bundle Deployment','time':300,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_number}'})

															print(f"        Updating {mcm_id} ...", end = '')
															mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
															print(f" done.")
															print("\n    Please do the Dry-Run of the Bundle before sending the MCM for approvals.")
															os.remove(var_file)
														except Exception as e:
															print(f"        Issue creating the bundle, please create the bundle and update the MCM manually.\n        Error: {e}")
														print(f"        Please add your {mcm_id} to the Dockets (for Validation): ISD-BB (L1/L2)")
									else:
										print(f"     Error checking tiedown: MUDA could not retrieve Hercules config for {tiedown[tc]['br-cor'][0]}")
			

							br_region = muda_auxiliary.get_border_region(border_prestage_pending[0])
							date_plus_4_weeks = datetime.datetime.now() +  + datetime.timedelta(weeks = 4)
							date_plus_4_weeks = date_plus_4_weeks.strftime("%Y-%m-%d")
								
							templates = {}
							templates["br-tra"] = "br-tra-rsvp-ibgp-prestage-noshift"
							templates["br-ubq-tor"] = "br-ubq-rsvp-ibgp-prestage-no-tshift"
							templates["en-gct-f1br"] = "en-gct-br-pcn-default-tshift"
							templates["br-bib"] = "br-bib-pcn-default-no-tshift"
							templates["en-tra"] = "en-tra-h13-pcn-default-no-tshift"
							templates["br-lle"] = "br-lle-rsvp-ibgp-prestage-noshift"
							templates["br-rrr"] = "br-rrr-vc-cor-pcn"
							templates["br-cor"] = "br-cor-vc-cor-pcn"
							templates["br-dcr"] = "br-dcr-default"

							for br_layer in templates:
								br_pending = [x for x in border_prestage_pending if br_layer in x]
								if br_pending != []:
									br_group = nsm.get_devices_from_nsm(f"{br_site}-{br_layer}",state = ['OPERATIONAL','MAINTENANCE'])
									br_group.sort(key=lambda x: int(x.split("-r")[-1]))

									br_regex_list = []
									if br_layer == "br-dcr":#this layer requires a different MCM per device
										br_regex_list = br_pending
									elif br_group != []:#for any other layer it is just one MCM per layer
										br_regex_list = [muda_auxiliary.regex_from_list(br_group)]

									for br_regex in br_regex_list:
										print(bcolors.cyan,f"\n     >> {br_layer[0:6].upper()}:",bcolors.end,f"do you want to create ManualPCN MCM for {br_regex} ", end="")
										time.sleep(0.1)
										answer = input("(y/n)? [n]: ") or "n"
										if answer == "y":
											print(f"        Pending {br_layer} devices: {br_group}")
											mcm_type = "manualpcn_prestage_" + br_layer.replace("-","")[0:5]

											mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation(mcm_type,br_regex,brick['brick'],brick['gb_cr'])
											mcm_id_list.append(mcm_id)
											if mcm_id:
												print(f"        Created {mcm_id}.")

												if br_layer == "br-dcr":
													nsm_queries = br_regex
												else:
													nsm_queries = "{}-{}".format(br_site,br_layer)

												if ("-en-tra" in nsm_queries or "-en-gct-" in nsm_queries) and (br_region != "bjs" and br_region != "zhy"):
													border_region = "iad"
												else:
													border_region = br_region

												generate_command = f"/apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign create --deadline '{date_plus_4_weeks} 14:00' --template {templates[br_layer]} --nsm-queries '{border_region}#{nsm_queries}' --metadata 'mcm={mcm_id}'"
												print(f"        Creating PCN Campaing (give it a few minutes). Executing:\n           {generate_command}")

												try:
													output_bytes = subprocess.check_output(generate_command, shell=True)
													output = output_bytes.decode("utf-8")
													campaing_number = output.split("https://hercules.amazon.com/campaign/")[1]
													campaing_number = campaing_number.split()[0]
													#campaing_number = "testing_campaing"
													print(f"        Campaign created: https://hercules.amazon.com/campaign/{campaing_number}")

													#print(f"        Reading Deployment Bundles from Campaign to fill out MCM overwive")
													#mw_cookie = mwinit_cookie.get_midway_cookie_obj()
													#kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
													#campaing_info = requests.get(f"https://hercules.amazon.com/campaign/{campaing_number}",auth=kerberos_auth, stream=True, headers={'Accept': 'application/json'}, cookies=mw_cookie)
													#campaign_string = campaing_info.content.decode('utf8')
													#dict = json.loads(campaing_info.content.decode('utf8'))

													hostnames = "\n".join(br_group)
													mcm_overview += f"""
#####Create Campaign Command\n{generate_command}\nCreated campaign {campaing_number}\n
#####Campaign ID\nhttps://hercules.amazon.com/campaign/{campaing_number}\n
#####Monitor Campaign Progress\nhttps://sphere.amazon.com/campaigndeployments/#/campaign/{campaing_number}\n
#####Deployments / Bundles\n{hostnames}\n
To view the campaign:\n\n    ssh {ncb}\n    /apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign get -c {campaing_number} -xd
\n\nTo approve the campaign:\n\n    ssh {ncb}\n    /apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign approve -c {campaing_number} -a border-pcn-campaign-l1-approver -m "Relevant approval message"\n
###Hostname or Service\n{hostnames}\n
###Timeline / Activity Plan
Steps to submit the campaign:\n\n    Ensure this CM is fully approved\n    Ensure all bundles in the CM are approved\n\n    ssh {ncb}\n    /apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign submit -c {campaing_number}\n
Check status of Submitted campaign:\n\n    ssh {ncb}\n    /apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign get -c {campaing_number}\n
Rollback Procedure\nFor ongoing Alfred deployment dispatched by PCN:\nAlfred will rollback if the CM causes dashboards to go red or any pre/post checks fail. Post check failure will initiate a full rollback. \nOnce the CM is done, to initiate rollback, the CRs identified as causing impact will have to be removed from GB, and alfred should be run in roll forward mode\n
To abort the PCN Campaign:\n\n    ssh {ncb}\n    /apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign abort -c {campaing_number}
"""

													steps = []
													#steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
													#steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
													steps.append({'title':'Submit Campaign','time':1,'description':f'ssh {ncb}\n/apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign submit -c {campaing_number}','rollback':f'To abort:\nssh {ncb}\n/apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign abort -c {campaing_number}\n\nNote: If a campaign is aborted while a deployment is in-flight, that deployment must be manually aborted from the hercules deployment UI. (same as alfred)\n\nFor ongoing Alfred deployment dispatched by PCN:\nAlfred will rollback if the CM causes dashboards to go red.\nOnce the CM is done, to initiate rollback, the CRs identified as causing impact will have to be removed from GB, and alfred should be run in roll forward mode'})

													print(f"        Updating {mcm_id} ...", end = '')
													mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
													print(f" done.")

													if br_layer == "br-rrr" or br_layer == "br-cor":
														print(f"        Please add your {mcm_id} to the Dockets (for Validation): ISD-BB (L1/L2).")
													elif br_layer == "br-dcr":
														print(f"        Please add your {mcm_id} to the Dockets (for Validation): Regional-Border-Deploy (L1/L2)")
													else:
														print(f"        Please add your {mcm_id} to the Dockets (for Validation): bne-internet-edge-l1 (L1), ISD (L1), DX-Deploy (L1/L2)")
												except:
													print("        Issue creating the campaign, please create the campaign and update the MCM manually.")
											else:
												print("        Issue creating the MCM.")

						if mcm_id_list != []:
							print("\n\n        When your ManualPCN MCMs are approved, follow these steps:")
							print("        - Edit Overview and set the Timing to the same of the campaign, starting now and end the expiration day in the campaign creation command.")
							print("        - Approve the L3-Scheduler manually, with reason 'PCN campaign override'.")
							print("        - Click on 'EXECUTE MCM'. It will show 'Submit Campaign', so click 'START STEP'.")
							print("        - Run the command in your MCM to submit the campaign (/campaign-service campaign submit ...).")
							print("        - PCN will try to execute your MCM withing that time frame, and when it is done, you will get an email and comment with 'Alfred deployment status is Successful'on your MCM.")

							print("\n        When your ManualPCN MCMs are is completed, follow thse steps:")
							print("        - Click 'Switch To Execution View'.")
							print("        - Click 'Complete Step' and then 'Complete MCM', select 'Successful' and comment a note 'Alfred deployment status is Successful'.")

							manualpcn = ",".join(mcm_id_list)
							print(f"\n        Updating MUDA step with pending devices to prestage and list of ManualPCN MCMs: {manualpcn}")
							ddb_table_update(brick['brick'],17,True,border_prestage_ready,border_prestage_pending,manualpcn)
						else:
							print("\n        Updating MUDA step with pending devices to prestage.")
							ddb_table_update(brick['brick'],17,True,border_prestage_ready,border_prestage_pending)


			else:
				print(f"          Unable to retrieve released config for {vccor}. Please make sure that the configurations are released.")


		##########################################################################################
		# 18 == VC-COR console, software and cabling validation
		elif int(brick['progress']) == 18:

			print(f"\n    (a) Look for the console information of your devices in NSM (https://nsm-iad.amazon.com/) and validate that you have access.")
			print("\n    (b) Make sure DCO upgraded your VC-COR to the valid JunOS version, or help DCO with the upgrade.\n        More info in MUDA Wiki.")
			print("\n    (c) Upgrade the FPGA/BIOS in the VC-COR.\n        More info in MUDA Wiki.")
			print("\n    (d) Make sure DCO completed the cabling between VC-COR and BR-KCT. You will validate the cabling in the Mobius Step, after the provisioning.")

			answer = input("\n        All the requirements above are ready? (y/n)? [n]: ") or "n"
			if answer == "y":
				print("        Moving to the next step.")
				ddb_table_update(brick['brick'],19,False)


		##########################################################################################
		# 19 == Ready to create GenevaBuilder kct_lagmember attributes for Brick and BR-KCT
		elif int(brick['progress']) == 19:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				gb_cr = brick['gb_cr'].split(",")[-1]
				merge_command = brick['merge_command']
				gb_path = user["gb_path"]
				print("\n        MUDA checks if the CR is merged in your local GB repo, so make sure that your GB repo is updated after the merge.")
				if cr.cr_status_closed(gb_path,gb_cr):
					print(f"        The {gb_cr} is already merged, moving to the next step.")
					ddb_table_update(brick['brick'],20,False)
				else:
					print(f"        The {gb_cr} is not merged yet.")
					print("        When it is approved, please merge it with:")
					print(bcolors.lightblue,"     {}".format(merge_command),bcolors.end)
					print("\n        IMPORTANT: when you merge this CR, you are blocking all the Border teams to do any work on these BR-KCT, because BR-KCT is bolted.")
					print("           RBE allows 3 days from the time you merge this CR, to the time you run the VC-COR Turn-Up MCM to push the changes.")
					print("           Only MERGE this CR when you are ready to work on the next steps: provisioning, mobius and VC-COR Turn-Up MCM.")

			#The CR/MCM was not created yet:
			else:
				port_reservation_nde = brick.get('port_reservation_nde')
			
				print(f"        Devices BR: {devices_br}\n        Devices Brick: {devices_brick}\n        Devices DX: {devices_dx}\n")

				method = None
				for brick_type in muda_data["gb_attributes_cr"]:
					if re.findall(brick_type,brick['brick']):
						method = muda_data["gb_attributes_cr"][brick_type]
						tool = method["tool"]
						break
				for br_type in muda_data["gb_attributes_cr"]:
					if re.findall(br_type,brick['br']):
						method = muda_data["gb_attributes_cr"][br_type]
						break
				else:
					br_type = None

				if method and peers!={}:
					created_files = {}

					print(f"\n>> Attribute creation for {brick['brick']} in {tool}.")
					if "GenevaBuilder" in tool:
						gb_path = os.path.expanduser("~")+"/"+tool
						print(bcolors.lightcyan,f"\n        {tool}: git status",bcolors.end)
						if cr.genevabuilder_git_status_ready(gb_path):
							print(f"        Your {tool} repository is clean.")
							print(bcolors.lightcyan,f"        {tool}: git pull --rebase",bcolors.end)
							cr.genevabuilder_git_pull(gb_path)
							print(f"\n        Your {tool} repository is updated now.")
							
							create_kct_lagmembers = True
							remove_port_reservation = False
							attr_modified = muda_genevabuilder.create_attributes(devices_brick,brick_type,peers,loopbacks,created_files,df,port_reservation_nde,remove_port_reservation,create_kct_lagmembers)
							if br_type:
								remove_port_reservation = True
								attr_br_modified = muda_genevabuilder.create_attributes(devices_brick,br_type,peers,loopbacks,created_files,df,port_reservation_nde,remove_port_reservation,create_kct_lagmembers)

							if attr_modified:
								print("\n>> Create GB kct_lagmembers CR for changes in Brick {} and {}.".format(brick['brick'],brick['br']))
								brick_groups = [brick['brick'],brick['br']]
								create_cr(brick_groups,peers,[],gb_path,{},19)#Updates the step

							else:
								print("\n>> No GB changes in Brick {}".format(brick['brick']))
								print(f"   Checking NSM status for {brick['brick']}.")
								operational_devices = []
								for device in devices_brick:
									operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
								op_devices = [x for x in devices_brick if x in operational_devices]
								if devices_brick == op_devices:
									print(f"   All the devices are operational. Moving to Step (28)")
									ddb_table_update(brick['brick'],28,False)
								else:
									print(f"   Not all the devices are operational. Moving to Step (22)")
									ddb_table_update(brick['brick'],20,False)

				else:
					print(f"        Your GB repository {gb_path} is not clean. Please clean it before creating a new CR. You can use 'git stash' and 'git clean -d -f' if you don't need the changes.")




		##########################################################################################
		# 20 == Waiting for gear console access and configuration.
		elif int(brick['progress']) == 20:

			brick_region = muda_auxiliary.get_border_region(brick['brick'])
			device_operational = nsm.get_devices_from_nsm(brick['brick'].split("[")[0],regions = [brick_region],state = ['OPERATIONAL'])
			device_provisioned = nsm.get_devices_from_nsm(brick['brick'].split("[")[0],regions = [brick_region],state = ['PROVISIONED'])
			device_pending = nsm.get_devices_from_nsm(brick['brick'].split("[")[0],regions = [brick_region],state = ['PENDING'])

			if device_operational != []:
				print("        Brick is OPERATIONAL in NSM, moving to Step (28)")
				ddb_table_update(brick['brick'],28,False)

			elif device_pending != []:
				print("        Brick is PENDING in NSM, moving to PROVISIONED.\n")
				for device in devices_brick:
					nsm.update_state_nsm(device, 'PROVISIONED', False, brick_region)#No Tracking TT required, sending False
				print("\n        Run MUDA again to confirm that the status was updated.")

			elif device_provisioned != []:
				print("        Brick is PROVISIONED in NSM, moving to the next step.")
				ddb_table_update(brick['brick'],21,False)

			else:
				device_list = mcm.mcm_get_hostnames_from_regex(brick['brick'])
				print("        Brick NOT in NSM yet, please complete the following manual tasks and try later:")

				stem = device_list[0].split("-r")[0]

				print("\n    -1- Generate the TShifted configuration from GB:")
				print(bcolors.lightblue,"              kinit -f",bcolors.end)
				print(bcolors.lightblue,"              cd ~/GenevaBuilder",bcolors.end)
				print(bcolors.lightblue,"              git pull --rebase",bcolors.end)
				print(bcolors.lightblue,'              ./gen.sh "{}" --extra-attrs=extra-attrs/tshift.attr --extra-attrs=extra-attrs/creds.attr'.format(brick['brick']),bcolors.end)
				
				print("\n    -2- Open a terminal session in your local computer, and copy the files to your Desktop:")
				for device in device_list:
					print(bcolors.lightblue,"              scp {username}@{ncb}:{path}/GenevaBuilder/out/{device}/all /Users/{username}/Desktop/{device}.conf".format(ncb = ncb, device = device, path = user["muda_path"], username = user["username"]),bcolors.end)

				my_username = user["username"]
				print("\n    -3- Copy/paste the configuration in each VC-COR via the console access:")
				print(bcolors.lightblue,f"              root@{device_list[0]}> exit",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}:~ # cat > baseconfig.conf",bcolors.end)
				print("                Paste the config here and exit with 'Ctrl+d', recommended to use iTerm2 in Mac with 'Edit>PasteSpecia>PasteSlowly'")
				print(bcolors.lightblue,f"              root@{device_list[0]}:~ # cli",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}> edit exclusive",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}# load override baseconfig.conf",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}# deactivate event-options",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}# deactivate system scripts",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}# commit check",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}# commit confirmed 15",bcolors.end)
				print("                Now type exit multiple times until getting the promt to log again in the router, and check the access with 'neteng' and the following password:")
				print("                ssh nebastion-iad")
				print("                /apollo/env/envImprovement/bin/odin-get com.amazon.networking.managed.prod.local-user.neteng")
				print(bcolors.lightblue,f"              root@{device_list[0]}# commit comment '{my_username}@ initial base config'",bcolors.end)
				print(bcolors.lightblue,f"              root@{device_list[0]}# request system reboot",bcolors.end)

				print("\n    -4- Add the VC-CORs to NSM manually (https://nsm-iad.amazon.com/) and they will show as PENDING:")
				for device in device_list:
					print(bcolors.lightblue,f"              {device}/{device[0:3]}/{brick['brick_loopbacks'][device]['PRIMARYIP']}/prod",bcolors.end)



		##########################################################################################
		# 21 == Waiting on Mobius test.
		elif int(brick['progress']) == 21:

			print("        Complete Mobius test using https://w.amazon.com/bin/view/DXDEPLOY_Automation_Others/Scripts/dx_mobius.py/")
			mobius_link = input("        Provide Mobius result link (https://mobiuschecker-pdx.pdx.proxy.amazon.com/topologies/62979/jobs/771815) or enter to skip: ") or "Empty"
			if "https://mobiuschecker" in mobius_link:
				print("        Saving Mobius result and moving to the next step.")
				#provide and save the Mobius
				ddb_table_update(brick['brick'],22,False,mobius_link)
			else:
				print("        Not a valid Mobius result.")


		##########################################################################################
		# 22 == Border/Brick prestage MCM.
		elif int(brick['progress']) == 22:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['mcm_border_prestage'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				if cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						print(f"\n   {last_mcm} is Completed Successful, moving to the next step.")
						ddb_table_update(brick['brick'],23,False)
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")
				
			#The CR/MCM was not created yet:
			else:
				print(f"        Checking Brick devices NSM status: {devices_brick}")
				operational_devices = []
				for device in devices_brick:
					operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
				op_devices = [x for x in devices_brick if x in operational_devices]

				if op_devices == devices_brick:
					print("        All the Brick devices are operational.")
					print(f"\n        Checking DX devices NSM status: {devices_dx}")
					operational_devices = []
					for device in devices_dx:
						operational_devices += nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
					non_op_devices = [x for x in devices_dx if x not in operational_devices]

					non_op_devices_connected = []
					print(f"        Non Operational DX Devices: {non_op_devices}")
					for peer in peers:
						device_a,device_z = peer.split("<>")
						if device_a in devices_brick and device_z in non_op_devices:
							non_op_devices_connected.append(device_z)
					non_op_devices = list(dict.fromkeys(non_op_devices_connected))
					non_op_devices.sort()
					print(f"        Non Operational DX Devices connected to the Brick: {non_op_devices}")

					dar_devices = [x for x in non_op_devices if '-vc-dar-' in x]
					if len(dar_devices) > 2:
						non_op_devices = [ x for x in non_op_devices if not '-vc-dar-' in x]
						
					if non_op_devices or "-br-agg-" in devices_brick[0]:################BR-TRA/VC-COR/BR-AGG BGP PRESTAGE FOR VC-BDR and ONLY 2 NEW VC-CAR/DAR (WE NEED TO UPDATE TEMPLATE)

						print("\n        Preparing BGP Prestage MCM on Brick {} for new, non Operational, DX devices: {}".format(brick['brick'],non_op_devices))
						devices_brick = mcm.mcm_get_hostnames_from_regex(brick['brick'])
						devices_brick_new = []
						for device in devices_brick:
							for peer in peers:
								if device in peer.split("<>"):
									devices_brick_new.append(device)
									break
						devices_brick = devices_brick_new

						method = False
						for device_type in muda_data["bgp_prestage_mcm"]:
							if re.findall(device_type,brick['brick']):
								method = muda_data["bgp_prestage_mcm"][device_type]
								break

						devices_brick.sort()
						non_op_devices.sort()
						devices_brick_regex = muda_auxiliary.regex_from_list(devices_brick)
						non_op_devices_regex = muda_auxiliary.regex_from_list(non_op_devices)
						gb_cr = brick['gb_cr'].split(",")[-1]
						mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("border_bgp_prestage",devices_brick_regex,non_op_devices_regex,gb_cr,method["policy"])

						if mcm_id:
							print("\n>>",bcolors.lightcyan,f"{mcm_id}",bcolors.end," created")

							list_device = []
							list_generate_command = []
							list_bundle_number = []
							steps = []
							steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
							steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})

							for device in devices_brick:
								print("\n>>",bcolors.lightcyan,f"{device}",bcolors.end,"creating",bcolors.lightcyan,"VAR",bcolors.end,f"file to {non_op_devices}")

								site = device.split("-")[0]
								gb_path = user["gb_path"]

								border_folder = muda_auxiliary.get_border_folder(device)
								if "-br-agg-" in device:
									attr = gb_path + "/targetspec/" + border_folder + "/" + device + f"/customer-vpc-{device[0:3]}.attr"
								else:
									attr = gb_path + "/targetspec/" + border_folder + "/" + device + "/dxpeer.attr"

								print(f"    {attr}")

								new_lags,new_lags_unit_10,new_groups,new_loopbacks,new_p2p,new_peers,new_interfaces,old_lags,old_lags_unit_10 = muda_genevabuilder.read_attributes(attr,non_op_devices)

								if "-br-agg-" in device:
									policy_change_variables = ""

									first_vc_bar = non_op_devices[0]
									connected_vc_edg = []
									for peer in peers:
										device_a,device_z = peer.split("<>")
										if first_vc_bar == device_a and "-vc-edg-" in device_z:
											if device_z not in connected_vc_edg:
												connected_vc_edg.append(device_z)
									vc_edg_loopbacks = [loopbacks[x]["PRIMARYIP_CS"]+"/32" for x in connected_vc_edg]

									device_interfaces = nsm.get_device_interfaces_from_nsm(device)
									local_cor = "NOT_FOUND"
									for interface in device_interfaces:
										if interface.get("Neighbor"):
											if "-br-dcr-" in interface["Neighbor"]:
												local_cor= interface["Neighbor"].split("-")[0]
												break

								#On BR-TRA with existing LAGs, we have to set the variable 'policy_change_for_car' if there are changes in the policy for existing LAGs
								elif "-br-tra-" in device and old_lags:
									#Create existing_dxpeer_groups with the DXPEER groups for existing LAGs
									existing_dxpeer_groups =[]
									for lag in old_lags:
										with open(attr, "r") as f:
											for line in f:
												found_group = re.findall(r"DXPEER DXPEERNAME (.*) REMDEVICE.*IFLAGDXPEER {}$".format(lag),line)
												if found_group:
													existing_dxpeer_groups.append(found_group[0])
									print(f"\n    Detected pre-existing LAGs {old_lags} which use the DXPEER groups {existing_dxpeer_groups}.")

									#Checking if the existing DXPEER group has the old policy, in which case we need to set 'policy_change_for_car=true'
									dxpeer_group = existing_dxpeer_groups[0]
									print(f"      Checking if the DXPEER group {dxpeer_group} has the updated policy (DX-AWS-INT-CUST-OVERRIDE):")
									config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
									if config != None:
										config = config.decode().replace(' ', '')
										config = config.replace('\n', '')
										
										if re.findall(r"(setprotocolsbgpgroupEBGP-{}importDX-AWS-INT-CUST-OVERRIDE)".format(dxpeer_group),config):
											print(f"      Updated policy found, setting 'policy_change_for_car' variables:")
											policy_change_variables = "policy_change_for_car=False"
											print(policy_change_variables)
										else:
											print(f"      Updated policy NOT found, setting 'policy_change_for_car' variables:")
											#Create Variables required for when 'policy_change_for_car' is True
											directconnect_bgp_group_for_policy_testing = ""
											existing_vc_car_inet_p2p_ip = ""
											existing_vc_car_ipv6_p2p_ip = ""
											existing_vc_car_peers = []
											for existing_dxpeer_group in existing_dxpeer_groups:
												if directconnect_bgp_group_for_policy_testing == "":
													directconnect_bgp_group_for_policy_testing = existing_dxpeer_group
												with open(attr, "r") as f:
													for line in f:
														found_group = re.findall(r"DXPEER DXPEERNAME {} REMDEVICE.*REMIPADDR ([0-9\.\/]+)$".format(existing_dxpeer_group),line)
														if found_group:
															existing_vc_car_peers.append(found_group[0])
															if existing_vc_car_inet_p2p_ip == "":
																existing_vc_car_inet_p2p_ip = found_group[0]
														found_group = re.findall(r"DXPEER DXPEERNAME {} REMDEVICE.*REMIPV6ADDR ([a-f0-9\:\/]+)$".format(existing_dxpeer_group),line)
														if found_group:
															existing_vc_car_peers.append(found_group[0])
															if existing_vc_car_ipv6_p2p_ip == "":
																existing_vc_car_ipv6_p2p_ip = found_group[0]
											policy_change_variables = """policy_change_for_car=True
DIRECTCONNECT_BGP_GROUP_FOR_POLICY_TESTING={}
EXISTING_VC_CAR_INET_P2P_IP={}
EXISTING_VC_CAR_IPV6_P2P_IP={}
EXISTING_VC_CAR_PEERS={}""".format(directconnect_bgp_group_for_policy_testing,existing_vc_car_inet_p2p_ip,existing_vc_car_ipv6_p2p_ip,",".join(existing_vc_car_peers))
											print(policy_change_variables)
								else:
									policy_change_variables = "policy_change_for_car=False"

								#Get the MTU for existing LAGs in the collected config
								if "-vc-cor-" in device:
									print("\n    VC-COR: is a Bolted device, so it pushes the ALL file and it always requires TShift.")
									tshift_needed = True
								elif "-br-agg-" in device:
									print("\n    BR-AGG: is a Bolted device, so it pushes the ALL file and it always requires TShift.")
									tshift_needed = True
								elif "-br-tra-" in device:
									print("\n    BR-TRA: if the MTU on any existing LAG public interface (unit 10) is 1500, the Bundle requires TShift.")
									tshift_needed = False
									print(f"    Checking MTU from HCS Collected for any existing LAG from DXPEER: {old_lags}")
									config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
									if config != None:
										config = config.decode().replace(' ', '')
										config = config.replace('\n', '')
										for lag in old_lags:
											try:
												pattern = "setinterfaces"+lag+"unit10familyinetmtu"
												splitted = config.split(pattern)[1]
												mtu = int(splitted.split("set")[0])
											
												if mtu == 1500:
													tshift_needed = True
													print(f"      MTU for existing LAG {lag}.10 is {mtu} in Collected config, required TShift.")
												else:
													print(f"      MTU for existing LAG {lag}.10 is {mtu} in Collected config, no TShift required.")
											except:
												print(f"      ERROR: MTU not found for existing LAG {lag}.10 in Collected config, no TShift required.")

								bundle_policy = method["policy"]
								if tshift_needed:
									bundle_policy = bundle_policy.replace(".yaml",".yaml --tshift")
									print(f"    TShift is required, using Autocheck Policy {bundle_policy}")
								else:
									print(f"    TShift is NOT required, using Autocheck Policy {bundle_policy}")

								if "-vc-cor-" in device:
									is_vccor = "true"
									is_brtra = "false"
									is_mx = "true"#nsm will show 'Model': 'jnp10003' so it doesn't contain mx
								elif "-br-tra-" in device:
									is_vccor = "false"
									is_brtra = "true"
									device_details = nsm.get_devices_detail_from_nsm(device)
									for d_detail in device_details[0]:
										if d_detail["Name"] == device:
											if "mx" in d_detail["Model"]:
												is_mx = "true"
											else:
												is_mx = "false"
											break

								lags_exists_towards_car = False
								mtu_9100_check = False
								if old_lags_unit_10:
									lags_exists_towards_car = True
									if not tshift_needed:
										mtu_9100_check = True

								if "-br-tra-" in device or "-vc-cor-" in device:
									content = """DEVICE_NAME={}
AE_TO_VC_DEVICES={}
TSHIFT={}
LAGS_EXISTS_TOWARDS_CAR={}
MTU_9100_CHECK={}
PUBLIC_INTERFACE_LIST_EXISTING_VLAN10={}
PUBLIC_INTERFACE_LIST_NEW_VLAN10={}
CAR1_CSC_BGP_GROUP={}
CAR2_CSC_BGP_GROUP={}
DIRECTCONNECT_BGP_GROUP_NEW_CAR1={}
DIRECTCONNECT_BGP_GROUP_NEW_CAR2={}
INTERFACES_TO_TURNUP={}
IPV4_P2P={}
VC_LOOPBACK={}
LAGS_EXIST=true
LAGS_NOT_EXIST=false
NEW_VC_DEVICE=true
NOT_NEW_VC_DEVICE=false
LOCAL_COR={}-br-cor-r1
IS_BR_DEVICE_AGG=false
IS_BR_DEVICE_TRA={}
IS_VC_COR={}
IS_MX_DEVICE={}
""".format(device,",".join(new_lags),tshift_needed,lags_exists_towards_car,mtu_9100_check,",".join(old_lags_unit_10),",".join(new_lags_unit_10),non_op_devices[0].upper(),non_op_devices[1].upper(),new_groups[0],new_groups[1],",".join(new_interfaces),",".join(new_p2p),",".join(new_loopbacks),site,is_brtra,is_vccor,is_mx)

								elif "-br-agg-" in device:
									content = """AE_TO_VC_DEVICES={}
CHECK_PHYSICAL_INTERFACE_STATE_UP_DOWN=false
EXISTING_LAGS=false
IS_BR_DEVICE_AGG=true
IS_BR_DEVICE_TRA=false
L3VPN_VARIANCE=10
LOCAL_COR={}-br-cor-r1
NEW_LAGS_EXIST=false
NEW_LAGS_NOT_EXIST=true
NEW_VC_DEVICE=true
NOT_NEW_VC_DEVICE=false
NO_NEW_LOGICAL_INTERFACES=true
IPV4_P2P={}
PEER_IP_ADDRESS_AGG_R1={}
VC_LOOPBACK={}
SITECAST_ENABLE=false
TIEDDOWN_ENABLE=false
""".format(",".join(new_lags),local_cor,",".join(new_p2p),",".join(new_peers),",".join(vc_edg_loopbacks))

								content = content + policy_change_variables
								var_file = user["muda_path"]+"/MUDA/"+device+".var"
								f = open(var_file, "w")
								f.write(content)
								f.close()
								print(f"\n    VAR file created: {var_file}\n{content}\n")

								generate_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern "/{}/" --modules {} --policy {} --policy-args-file {}.var --approvers {} --stream released'.format(device,method["modules"],bundle_policy,device,method["approvers"])
							
								print("\n>>",bcolors.lightcyan,f"{device}",bcolors.end,"creating",bcolors.lightcyan,"BUNDLE",bcolors.end)
								print(f"    Creating Alfred Bundle, please wait 5 minutes. Executing command:\n    {generate_command}")

								try:
									pwd = os.getcwd()
									command = "cp {} {}".format(var_file,pwd+"/"+device+".var")
									executed = subprocess.check_output(command, shell=True)

									output_bytes = subprocess.check_output(generate_command, shell=True)
									output = output_bytes.decode("utf-8")
									bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
									bundle_number = bundle_number.split()[0]

									list_device.append(device)
									list_generate_command.append(generate_command)
									list_bundle_number.append(bundle_number)
									print(f"        Bundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")
									command = "rm {}".format(pwd+"/"+device+".var")
									executed = subprocess.check_output(command, shell=True)
									os.remove(var_file)
								except Exception as e:
									print(f"        Issue creating the bundle, please create the bundle and update the MCM manually.\n        Error: {e}")
						
							else:#When the For loop created all the bundles
								mcm_overview += "####Bundle Generation:\n"
								for generate_command in list_generate_command:
									mcm_overview += f"```\n{generate_command}\n```\n"
								mcm_overview += "\n####Bundle Diffs/Config/Autochecks:\n"
								for x in range(0,len(list_device)):
									mcm_overview += f"Bundle for {list_device[x]}:  https://hercules.amazon.com/bundle-v2/{list_bundle_number[x]}\n"
								mcm_overview += "\n####Bundle Deployment:\n"
								for x in range(0,len(list_device)):
									mcm_overview += f"Deployment for {list_device[x]}:  /apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {list_bundle_number[x]}\n"
								for x in range(0,len(list_device)):
									steps.append({'title':f'Alfred Bundle Deployment {list_device[x]}','time':300,'description':f'To deploy the bundle:\nhttps://hercules.amazon.com/bundle-v2/{list_bundle_number[x]}\n\nExecute the following:\n/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {list_bundle_number[x]}\n\nTo rollback:\n/apollo/env/AlfredCLI-2.0/bin/alfred rollback -i <deployment HDS ID> -l <location> -r <reason>'})
								mcm_overview += "\n####Bundle Dry-Run Result:\n"
								for x in range(0,len(list_device)):
									mcm_overview += f"Dry-Run result for {list_device[x]}: [ENTER_DRYRUN_LINK_HERE]\n"

								print(f"\n        Updating {mcm_id} ...", end = '')
								mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
								print(f" ready. Updating step.")
								print("\n    Please do the Dry-Run of the Bundle before sending the MCM for approvals.")
								print("       For VC-COR changes, use Docket 'DX-Deploy'\n       For BR-TRA changes, use Docket 'IED-BR-TRA'\n       For BR-KCT/BR-AGG changes, use Docket 'Regional-Border-Deploy'")

								if "-br-agg-" in devices_brick[0]:
									print("\n    ATTENTION: BR-AGG has AutoPCN so you might not need this MCM, check the changes in the bundle.")
									print("    In the case that you want to get this MCM reviewed/deployed, please review if the variables 'SITECAST_ENABLE' and 'TIEDDOWN_ENABLE' are correct for the bundle.")
									print("    MUDA sets those 2 variables to 'False' by default, but, since BR-AGG is Bolted, you might have Tiedown/Sitecast changes, in which case you have to update the bundle.")

								ddb_table_update(brick['brick'],22,True,mcm_id)
						else:
							print("        Issue creating the MCM.")


					elif not non_op_devices:################SCALING: BR-TRA/VC-COR PRESTAGE
						print("        All the DX devices are Operational.\n        Checking if we are doing Scaling project.")
						new_dx_ports = brick.get('ports_to_shutdown')
						last_cutsheet = brick['cutsheet_mcm'].split(",")[-1]
						if new_dx_ports:
							print(f"\n>> We are scaling the following ports:")
							for device in new_dx_ports:
								print(f"   {device}: {new_dx_ports[device]}")
								#new_dx_ports = { Save this variable in DynamoDB for the future step
								#	"iad53-vc-car-r1": ["xe-0/0/1","xe-2/3/1"],
								#	"iad53-vc-car-r2": ["xe-0/0/4","xe-2/3/4"]
								#	}
							brick_type = brick['brick'].split("-")[1:3]
							brick_type = "-".join(brick_type).upper()
							print(f"\n>> Please create the Scaling Prestage MCM on {brick_type} using D-TOOL.")
							#command = "/apollo/env/DXDeploymentTools/bin/vc_scaling.py"
							#/apollo/env/DXDeploymentTools/bin/vc_scaling.py --car_to_tra --cr_prsv CR-26884187 --existing_lag --bundle_only
							#/apollo/env/DXDeploymentTools/bin/vc_scaling.py --car_to_tra --cr_link_add CR-26884187 --new_lag 
							#print(f"     {command}")

							print("   Instructions: https://w.amazon.com/bin/view/DXDEPLOY/Runbooks/VC-CAR_NR_Layer_Scaling_Procedure/#HStep-9:ScalingMCM-BR-TRA:")
							mcm_id = input("\n>> Enter the MCM number (MCM-00000000) or press Enter to stay in the current step: ") or "n"
							if re.findall("^MCM-[0-9]+$",mcm_id):
								print(f"   Updating step.")
								ddb_table_update(brick['brick'],22,True,mcm_id)
					
					else:
						print("\nERROR: More than 2 devices are NON operational, the Bundle Templates are not ready for this scenario, get suppoort from #muda-suppoort and update the templates.")



				################VC-COR DEPLOYMENT: BR-KCT PRESTAGE
				else:
					gb_cr = brick['gb_cr'].split(",")[-1]
					print(f"        VC-COR GenevaBuilder CR {gb_cr} is merged, Border Layer prestage is done and ports between VC-COR<>BR-KCT are ready.",bcolors.end)

					lags_released = []
					lags_collected = []
					device = mcm.mcm_get_hostnames_from_regex(brick['br'])[0]
					print(f"        Checking LAGs configured in {device} towards VC-COR")

					try:
						site = device.split("-")[0]
						lag_to_vccor = {}
						config = hercules.get_latest_config_for_device(device,"released")
						if config != None:
							config = config.decode().replace(' ', '')
							lag_to_vccor = re.findall(r'description"{}(ae[0-9]*)-->.*({}.*vc-cor-b\d+-r\d+)'.format(device,site),config)
							if lag_to_vccor != []:
								lags_released = [x for (x,y) in lag_to_vccor]
								vccor_released = [y for (x,y) in lag_to_vccor]
								print(f"        LAGs released in {device} to VC-COR: {lags_released}")
							else:
								print(f"        LAGs released in {device} to VC-COR: None")

						config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
						if config != None:
							config = config.decode().replace(' ', '')
							if re.findall(r'description"{}(ae[0-9]*)-->.*vc-cor'.format(device),config):
								lags_collected = re.findall(r'description"{}(ae[0-9]*)-->.*vc-cor'.format(device),config)
								print(f"        LAGs collected in {device} to VC-COR: {lags_collected}")
							else:
								print(f"        LAGs collected in {device} to VC-COR: None")

						if lags_released!=[]:
							lags_to_prestage = []
							vccor_to_prestage = []
							for i in range(0,len(lags_released)):
								if lags_released[i] not in lags_collected:
									lags_to_prestage.append(lags_released[i])
									vccor_to_prestage.append(vccor_released[i])

							if len(lags_to_prestage)>0:
								vccor_to_prestage.sort()
								vccor_to_prestage_regex = muda_auxiliary.regex_from_list(vccor_to_prestage)

								print(f"\n        We have to create BR-KCT Prestage MCM to Prestage LAGs {lags_to_prestage} to turnup {vccor_to_prestage_regex}")

								var_file_name = brick['brick'].split("-b")[0] + "_turnup.var"
								var_file_name = var_file_name.replace("-","_")
								var_file = create_var_file_turnup(vccor_to_prestage,brick['br'],var_file_name,peers,loopbacks)
								
								if var_file:
									print("\n        The VAR file was created, creating now the MCM and the Alfred Bundle")

									mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("brkct_vccor_prestage",brick['br'],vccor_to_prestage_regex,gb_cr)
									if mcm_id:
										print(f"        Created {mcm_id}.")
										var_file = user["muda_path"]+ "/MUDA/" + var_file_name
										with open(var_file, 'r') as file :
											filedata = file.read()
										filedata = filedata.replace('MCM-00000000', mcm_id)
										with open(var_file, 'w') as file:
											file.write(filedata)

										generate_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern "/{}/" --modules all --replace-all-config --preserve-acls --policy unified_kct_lag_turnup.yaml --policy-args-file {} --approvers neteng-is-dply-l1-approver --stream released'.format(brick['br'],var_file)
										print(f"        Creating Alfred Bundle, please wait 5 minutes. Executing command:\n           {generate_command}")

										try:
											output_bytes = subprocess.check_output(generate_command, shell=True)
											output = output_bytes.decode("utf-8")
											bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
											bundle_number = bundle_number.split()[0]

											print(f"        Bundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")

											mcm_overview += f"####Bundle Generation:\n{generate_command}\n"
											mcm_overview += f"\n####Bundle Diffs/Config/Autochecks:\nhttps://hercules.amazon.com/bundle-v2/{bundle_number}\n"
											mcm_overview += f"\n####Bundle Deployment:\n/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_number}\n"
											mcm_overview += "\n####Bundle Dry-Run Result:\n[ENTER_DRYRUN_LINK_HERE]\n"

											steps = []
											steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
											steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
											steps.append({'title':'Alfred Bundle Deployment','time':300,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_number}'})

											print(f"        Updating {mcm_id} ...", end = '')
											mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
											print(f" ready. Updating MUDA step.")
											print("\n    Please do the Dry-Run of the Bundle before sending the MCM for approvals.")
											print("   Then, use Docket 'DX-Deploy' for L1/L2 and when that is approved, add it to 'regional-border-engineering-l1', and finally to 'regional-border-engineering-l3'")
											ddb_table_update(brick['brick'],22,True,mcm_id,lags_to_prestage)
											os.remove(var_file)
										except Exception as e:
											print(f"        Issue creating the bundle, please create the bundle and update the MCM manually.\n        Error: {e}")
									else:
										print("        Issue creating the MCM.")
								else:
									print(f"        Issue creating VAR file for {device}")
							else:
								print(f"        All the LAGs in released exist in collected, so BR-KCT Prestage turn-up is done, moving to the next step.")
								ddb_table_update(brick['brick'],23,False)
						else:
							print(f"        No LAGs found in released config for {device}")
					except:
						print(f"        Unable to retrieve Hercules config for {device}")



		##########################################################################################
		# 23 == ACLManage MCM creation for deployments on existing VC-COR/BR-TRA after BGP Prestage
		elif int(brick['progress']) == 23:

			completed_and_operational = False
			completed_and_not_operational = False
			brick_operational = True
			if re.findall("-vc-cor-",brick['brick']):
				brick_region = muda_auxiliary.get_border_region(brick['brick'])
				devices_brick = mcm.mcm_get_hostnames_from_regex(brick['brick'])
				devices_operational = nsm.get_devices_from_nsm(brick['brick'].split("[")[0],regions = [brick_region],state = ['OPERATIONAL','MAINTENANCE'])
				devices_oper = [x for x in devices_brick if x in devices_operational]
				devices_brick.sort()
				devices_oper.sort()
				if devices_brick != devices_oper:
					print("\n    The VC-COR Brick is NOT operational.")
					brick_operational = False
				else:
					print("\n    The VC-COR Brick is operational.")

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['mcm_aclmanage'].split(",")[-1]
				if check_mcm_completed_successful(last_mcm,modeledcm):
					if not brick_operational:
						print(f"\n>> The MCM was completed on a NOT OPERATIONAL Brick, there are some manual tasks that you have to do:")
						print(bcolors.lightcyan,f"\n   (a) MANUAL DEPLOYMENT:",bcolors.end,"open",bcolors.lightcyan,"https://acl-manage.amazon.com",bcolors.end,"\n       On the top banner 'Regional Endpoints' select the Endpoint for your region, and click on 'Deploy ACL'.\n       Select one of the ACL for your device, for instance 'ACL6:BorderInDirectConnect' and click 'Search for Devices'.\n       Select your VC-COR devices where you executed the MCM.\n       Select 'No Velocity' and 'Debug', and click on 'Deploy All ACLs'.\n       It will ask you for a MasterTT (create one if you don't have it) in the format 'TT:0123456789', a comment 'Deploying ACL' and Fabric is 'None'.")
						print(bcolors.lightcyan,f"\n   (b) AUTO DEPLOYMENT:",bcolors.end,"once the Manual deployment is completed from the previous task, you have to toggle it to Auto.\n       Open",bcolors.lightcyan,"https://acl-manage.amazon.com",bcolors.end,"\n       On the top banner 'Regional Endpoints' select the Endpoint for your region, and click on 'Show Scopes'.\n       Look for the 'VC-COR' scope, and if it is in 'manual', click on 'Toggle Scope Type' to change it to auto.")
						answer = input(f"\n>> Are the previous manual tasks completed (y/n)? [n]: ") or "n"
						if answer == "y":
							completed_and_not_operational = True
					else:
						completed_and_operational = True

			#The CR/MCM was not created yet:
			else:
				ready_to_create_mcm = True
				if not brick_operational:
					print("\n>> Before creating the ACLManage MCM on NOT OPERATIONAL VC-COR:")
					print(bcolors.lightcyan,f"\n   (a) CHECK SCOPE:",bcolors.end,"make sure the Scope is created for your Region.\n       Open",bcolors.lightcyan,"https://acl-manage.amazon.com",bcolors.end,"\n       On the top banner 'Regional Endpoints' select the Endpoint for your region, and click on 'Show Scopes'.\n       Make sure that there is a 'VC-COR' scope created, and that the regex matches your site.\n       If you are creating a new Region or a new TC in a Region, it will be probably missing.\n       To add/modify a Scope, open a TT like https://t.corp.amazon.com/V175098964")
					answer = input(f"\n>> Is the Scope ready (y/n)? [n]: ") or "n"
					if answer != "y":
						ready_to_create_mcm = False
				
				if ready_to_create_mcm:
					bgp_prestaged = True
					required_mcm,mcm_id = create_aclmanage_mcm(peers,loopbacks,devices_br,devices_brick,devices_dx,bgp_prestaged,brick_operational)
					if mcm_id:
						if brick_operational:
							print(bcolors.red,f"\n>> WARNING, manual work:",bcolors.end,"to run this MCM, the ports between VC-COR/BR-TRA and VC-CAR/DAR must be DOWN.")
							print("       If the new VC-CAR/DAR gear is already installed and those ports are UP, you have to shut them DOWN from the VC-CAR/DAR side.")
							print("       And because the BGP Prestage is done, shutting down those ports causes a Sev2 TT, unless you NARG the upstream VC-COR/BR-TRA ports, using:")
							print(bcolors.lightcyan,"      https://bladerunner.amazon.com/workflows/batch_narg_hostname_interface/versions/prod",bcolors.end)
							print("       Since the NARG is associated to a TT, to remove the NARG when you are done, move the TT to 'Resolved' or to 'Pending Verification or Fix'")

							answer = input("\n       Press Enter to continue...")

						print(f"\n>> Created {mcm_id}. Updating MUDA step.")
						ddb_table_update(brick['brick'],23,True,mcm_id)

					elif not required_mcm:
						print("\n>> ACLManage MCM not required at this time.")
						if brick_operational:
							completed_and_operational = True
						else:
							completed_and_not_operational = True
					else:
						print("\n>> Issue creating MCM.")

			if completed_and_not_operational:
				print("       Brick is NOT OPERATIONAL, moving to the next step.")
				ddb_table_update(brick['brick'],24,False)

			if completed_and_operational:
				if re.findall("-br-tra-",brick['brick']):
					print(bcolors.red,f"\n>> IMPORTANT:",bcolors.end," since BGP Prestage and ACLManage are completed on BR-TRA, please create a CR to remove the TURNUP flag from the dxpeer.attr. This part is not automated yet. You just need the CR approved, no MCM is required after that.\n   More info https://w.amazon.com/bin/view/DX_Deployment_Border#HClean-upTURNUPflagonBR-TRA")
					answer = input(f"\n>> Is the previous manual task completed (y/n)? [n]: ") or "n"
					if answer != "y":
						completed_and_operational = False
				if completed_and_operational:
					print("       Brick is OPERATIONAL, moving to Step (28).")
					ddb_table_update(brick['brick'],28,False)

		##########################################################################################
		# 24 == Waiting for VC-COR Herbie prevalidation.
		elif int(brick['progress']) == 24:
			print("\n   Please follow the instructions in MUDA wiki to upload SLAX files and do the Herbie pre-validation.")
			print(bcolors.lightcyan,"\n    (a) UPLOAD SLAX FILES.",bcolors.end)
			print(bcolors.lightcyan,"\n    (b) HERBIE PRE-VALIDATION:",bcolors.end,"use https://herbie.corp.amazon.com/run_device_validation")

			answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
			if answer == "y":
				print("       Moving to the next step.")
				ddb_table_update(brick['brick'],25,False)

		##########################################################################################
		# 25 == Ready to create BR-KCT Normalization CR.
		elif int(brick['progress']) == 25:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				gb_cr = brick['gb_port_normalization_cr'].split(",")[-1]
				merge_command = brick['merge_command']
				gb_path = user["gb_path"]
				print("\n        MUDA checks if the CR is merged in your local GB repo, so make sure that your GB repo is updated after the merge.")
				if cr.cr_status_closed(gb_path,gb_cr):
					print(f"        The {gb_cr} is already merged, moving to the next step.")
					ddb_table_update(brick['brick'],26,False)
				else:
					print(f"        The {gb_cr} is not merged yet.")
					print("        When it is approved, please merge it with:")
					print(bcolors.lightblue,"     {}".format(merge_command),bcolors.end)

			#The CR/MCM was not created yet:
			else:
				lags_to_normalize = brick['lags_to_prestage']
				gb_path = user["gb_path"]
				print(bcolors.lightcyan,"        GB running: git status",bcolors.end)
				if cr.genevabuilder_git_status_ready(gb_path):
					print(f"        Your GB repository {gb_path} is clean. Doing git pull --rebase")
					print(bcolors.lightcyan,"        GB running: git pull --rebase",bcolors.end)
					cr.genevabuilder_git_pull(gb_path)

					border_folder = muda_auxiliary.get_border_folder(brick['brick'])
					attr = user["gb_path"] + "/targetspec/"+ border_folder +"/shared/" + brick['br'].split("-r[")[0] + "-if.attr"
					f = open(attr, "r")
					file =  f.read()
					f.close()

					lags_to_normalize = [x for x in lags_to_normalize if f"IFLAG {x} OSPFMETRIC 65000" in file]
					print(f"\n   Normalizing LAGs with OSFPMETRIC 65000 to 50: {lags_to_normalize}")
					for lag in lags_to_normalize:
						old_line = f"IFLAG {lag} OSPFMETRIC 65000"
						new_line = f"IFLAG {lag} OSPFMETRIC 50"
						print(f"    {old_line} >>> {new_line}")
						file = file.replace(old_line,new_line,1)

					f = open(attr, "w")
					f.write(file)
					f.close()

					cr_title = "[DX][MUDA][{}] Border LAG normalization for VC-COR brick {}".format(brick['brick'].split("-")[0].upper(),brick['brick'])
					dockets = "Regional-Border-Deploy"

					commit_command = "git commit -m '" + cr_title + "'"
					print(bcolors.lightcyan,"        GB running: git add .",bcolors.end)
					print(bcolors.lightcyan,f"        GB running: {commit_command}",bcolors.end)
					cr.genevabuilder_git_add_commit(gb_path,commit_command)

					command = '/apollo/env/ReleaseWorkflowCLI/bin/generate_configs.py --devices "{}" --cr --dockets {}'.format(brick['br'],dockets)
					print(bcolors.lightcyan,f"        GB running: {command}",bcolors.end)
					print("        Please wait 10 minutes")
					gb_cr = cr.genevabuilder_generate_configs(gb_path,command)

					if gb_cr:
						merge_command = '/apollo/env/GitLocker/bin/gitlocker.py --devices "{}" --cr {}'.format(brick['br'],gb_cr)
						print("     Please review and publish your CR:")
						print(bcolors.lightblue,"     https://code.amazon.com/reviews/{}\n".format(gb_cr),bcolors.end)
						ddb_table_update(brick['brick'],25,True,gb_cr,merge_command)

				else:
					print(f"        Your GB repository {gb_path} is not clean. Please clean it before creating a new CR. You can use 'git stash' and 'git clean -d -f' if you don't need the changes.")




		##########################################################################################
		# 26 == Ready to create BR-KCT Normalization MCM.
		elif int(brick['progress']) == 26:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['mcm_border_normalization'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				if cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						print(f"\n   {last_mcm} is Completed Successful, moving to the next step.")
						ddb_table_update(brick['brick'],27,False)
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")


			#The CR/MCM was not created yet:
			else:
				gb_cr = brick['gb_port_normalization_cr'].split(",")[-1]

				lags_to_normalize = brick['lags_to_prestage']
				vccors = mcm.mcm_get_hostnames_from_regex(brick['brick'])
				device = mcm.mcm_get_hostnames_from_regex(brick['br'])[0]
				print(f"        Checking LAG released/collected in {device} towards VC-COR")
				ready_to_normalize = True

				try:
					config = hercules.get_latest_config_for_device(device,"released")
					if config != None:
						config = config.decode().replace(' ', '')
						config = config.replace('\n', '')
						for lag in lags_to_normalize:
							if re.findall(r'ospf{{area0.0.0.0{{interface{}.0{{interface-typep2p;metric50;'.format(lag),config):
								print(f"           LAG {lag} has metric released 50, OK.")
							else:
								print(f"           LAG {lag} does not have metric released 50, BR-KCT Normalization MCM not created.")
								ready_to_normalize = False
								break

					config = hercules.get_latest_config_for_device(device,"collected",['set-config'])
					if config != None and ready_to_normalize:
						config = config.decode().replace(' ', '')
						config = config.replace('\n', '')
						for lag in lags_to_normalize:
							if re.findall(r'ospfarea0.0.0.0interface{}.0metric65000set'.format(lag),config):
								print(f"           LAG {lag} has metric collected 65000, OK.")
							else:
								print(f"           LAG {lag} does not have metric collected 65000, BR-KCT Normalization MCM not created.")
								ready_to_normalize = False
								break
				except:
					print(f"        Unable to retrieve Hercules config for {device}, BR-KCT Normalization MCM not created")
					ready_to_normalize = False

				if ready_to_normalize:
					print(f"\n        Checks are valid, ready to do BR-KCT Normalization MCM to normalize LAGs {lags_to_normalize} from 65000 to 50.")

					var_file_name = brick['brick'].split("-r[")[0] + "_normalization.var"
					var_file_name = var_file_name.replace("-","_")
					
					var_file = create_var_file_normalization(lags_to_normalize,brick['br'],var_file_name)
					if var_file:
						print("\n        The VAR file was created, creating now the MCM and the Alfred Bundle")
						mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("brkct_vccor_normalization",brick['br'],brick['brick'],gb_cr)
						if mcm_id:
							print(f"        Created {mcm_id}.")

							var_file = user["muda_path"]+ "/MUDA/" + var_file_name
							generate_command = '/apollo/env/AlfredCLI-2.0/bin/alfred bundle create --device-pattern "/{}/" --modules all --replace-all-config --preserve-acls --policy unified_kct_lag_normalization.yaml --policy-args-file {} --approvers neteng-is-dply-l1-approver --stream released'.format(brick['br'],var_file)
							print(f"        Creating Alfred Bundle (give it a few minutes). Executing:\n           {generate_command}")


							try:
								output_bytes = subprocess.check_output(generate_command, shell=True)
								output = output_bytes.decode("utf-8")
								bundle_number = output.split("https://hercules.amazon.com/bundle-v2/")[1]
								bundle_number = bundle_number.split()[0]

								print(f"        Bundle created: https://hercules.amazon.com/bundle-v2/{bundle_number}")

								mcm_overview += f"####Bundle Generation:\n{generate_command}\n"
								mcm_overview += f"\n####Bundle Diffs/Config/Autochecks:\nhttps://hercules.amazon.com/bundle-v2/{bundle_number}\n"
								mcm_overview += f"\n####Bundle Deployment:\n/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_number}\n"
								mcm_overview += "\n####Bundle Dry-Run Result:\n[ENTER_DRYRUN_LINK_HERE]\n"

								steps = []
								steps.append({'title':f'Inform IXOPS Oncall','time':5,'description':f'"inform the ixops oncall primary" (Check following link to get the current Primary details: https://nretools.corp.amazon.com/oncall/ )'})
								steps.append({'title':f'Start Monitoring Dashboards','time':5,'description':f'Start Monitoring "Darylmon all" and #netsupport Chime Room\nThis is to see any ongoing/newly coming Sev2s in AWS Networking\nYou need to monitor this through out the deployment of this MCM'})
								steps.append({'title':'Alfred Bundle Deployment','time':300,'description':f'/apollo/env/AlfredCLI-2.0/bin/alfred deploy -mcm {mcm_id} -b {bundle_number}'})

								print(f"        Updating {mcm_id} ...", end = '')
								mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)
								print(f" ready. Updating MUDA step.")
								print("\n    Please do the Dry-Run of the Bundle before sending the MCM for approvals.")
								print("   Then, use Docket 'DX-Deploy' for L1/L2 and when that is approved, add it to 'regional-border-engineering-l1', and finally to 'regional-border-engineering-l3'")
								ddb_table_update(brick['brick'],26,True,mcm_id,lags_to_normalize)
								os.remove(var_file)
							except:
								print("        Issue creating the bundle, please create the bundle and update the MCM manually.")
						else:
							print("        Issue creating the MCM.")
					else:
						print("       Issue creating the VAR file.")



		##########################################################################################
		# 27 == VC-COR Brick Handoff to IXOps
		elif int(brick['progress']) == 27:

			region = muda_auxiliary.get_border_region(brick['brick'])
			nsm_region = brick['brick'][0:3]
			herbie_pattern = brick['brick'].split("-r[")[0]

			print(bcolors.lightcyan,"\n\n>> Complete the following manual tasks following MUDA Wiki:",bcolors.end)
			print(bcolors.lightcyan,"\n    (a) UNSHIFT VC-COR:",bcolors.end,"using https://bladerunner.amazon.com/workflows/Traffic_shift_vc_device/versions/prod")
			print("            You need the TrackingTT, device names, region, and the action is 'back'")

			print(bcolors.lightcyan,"\n    (b) NSM OPERATIONAL:",bcolors.end,"go to NSM and do a manual 'Poll Device' on your VC-CORs")
			print("            Then, fill out the TrackingTT below and use these commands to change the NSM status from 'TURNED_UP' to 'OPERATIONAL':")
			print(f"               ssh nebastion-{region}")
			for device in devices_brick:
				print(f'               /apollo/env/NSMDarylPluginCLI/bin/nsm_cli.py updatestate --action MONITORING_ENABLED --cm "FILL_OUT_TRACKING_TT" {device} --user-log-to-stdout --fabric prod --region {nsm_region}')

			print(bcolors.lightcyan,"\n    (c) HERBIE VALIDATION:",bcolors.end,"go to https://herbie.corp.amazon.com/run_device_validation")
			print("               Select Template: vc-cor.yaml")
			print(f"               Enter NSM pattern: name:/{herbie_pattern}.*/")
			print("            Confirm that all the tests are successful, or troubleshoot if some test fails")

			answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
			if answer == "y":
				print(bcolors.lightcyan,"\n\n>> Creating IXOps Handoff MCM template.",bcolors.end)

				sostenuto_validation = ""
				validation_links = []#In the future we can automate validations
				
				mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("mcm_ixops_handoff",brick['brick'],sostenuto_validation,validation_links)
				print(f"        Created {mcm_id}.")
				steps = []
				steps.append({'title':f'Validate devices are ready for HandOff','time':30,'description':f'IXOps validation'})
				mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)

				print(f"\nATTENTION: Review {mcm_id} and update the Overview with the 'Project SIM' and the 'Herbie Validation' result link")
				print("           Then, send it for approval and add it to the 'aws-ix-ops' Docket.")
				print("           MUDA will continue will the deployment steps, and in parallel, the NDE must make sure the MCM is approved.")

				print("\nMoving to the next step.")
				ddb_table_update(brick['brick'],28,False,mcm_id)


		##########################################################################################
		# 28 == Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD console, software and cabling validation
		elif int(brick['progress']) == 28:
			print("\n    Follow the instructions in MUDA Wiki to complete these tasks:")
			print(f"\n    (a) Look for the console information of your devices in NSM (https://nsm-iad.amazon.com/) and validate that you have access.")

			if "-br-agg-" not in devices_brick[0]:
				print("\n    (b) Make sure that DCO upgraded your VC-CAR/CAS/DAR to the valid JunOS version, or help DCO with the upgrade.")
				print("\n    (c) Make sure DCO completed the cabling between VC-CAR/CAS/DAR and VC-COR/BR-TRA. You will validate the cabling in the Mobius Step, after the provisioning.")
				print("\n    (d) Add the console access information to ConsoleWiki https://w.amazon.com/index.php/EC2/Networking/IXOps/ConsoleAccess-VC-CAR")
			else:
				print("\n    (b) Make sure that DCO upgraded your VC-BAR/EDG to the valid JunOS version, or help DCO with the upgrade.")
				print("\n    (c) Make sure DCO completed the cabling between VC-BAR/EDG and BR-AGG. You will validate the cabling in the Mobius Step, after the provisioning.")

			answer = input("\n        All the requirements above are ready? (y/n)? [n]: ") or "n"
			if answer == "y":
				print("        Moving to the next step")
				ddb_table_update(brick['brick'],29,False)

		##########################################################################################
		# 29 == Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD provisioning.
		elif int(brick['progress']) == 29:
			print("\n    Follow the instructions in MUDA Wiki to complete these tasks:")

			if "-br-agg-" not in devices_brick[0]:
				print("\n    (a) Generate and download VC-CAR/CAS/DAR Configuration.")
				print("\n    (b) Apply configuration to VC-CAR/CAS/DAR.")
				print("\n    (c) Upload SLAX scripts.")
				print("\n    (d) Spawn Of Sauron validation.")
				print("\n    (e) Generate the SSL Certificates for VC-CAR/CAS.")
				print("\n    (f) Schedule the MMR Port Testing with DCO.\n        IMPORTANT: MMR Port Testing has to be completed by Step (32), but it doesn't block you to move to the following step now.")
			else:
				print("\n    (a) Generate and download VC-BAR/EDG Configuration.")
				print("\n    (b) Apply configuration to VC-BAR/EDG.")
				print("\n    (c) Load the BGP License file to QFX VC-BAR.")
				print("\n    (d) Upload SLAX scripts.")
				print("\n    (e) Spawn Of Sauron validation.")

			answer = input("\n        All the requirements above are ready? (y/n)? [n]: ") or "n"
			if answer == "y":
				print("        Moving to the next step")
				ddb_table_update(brick['brick'],30,False)

		##########################################################################################
		# 30 == Waiting for Phoenix/Centennial Mobius testing
		elif int(brick['progress']) == 30:

			print("\n    Use",bcolors.lightcyan,"dx_mobius.py",bcolors.end,"to validate the cabling between devices:")
			print("    https://w.amazon.com/bin/view/DXDEPLOY_Automation_Others/Scripts/dx_mobius.py/")

			answer = input("\n        Is the mobius validation completed? (y/n)? [n]: ") or "n"
			if answer == "y":
				print("        Moving to the next step")
				ddb_table_update(brick['brick'],31,False)

		##########################################################################################
		# 31 == iBGP Mesh
		elif int(brick['progress']) == 31:
			ibgp_mesh_mcm_incompleted =  []

			#Checks if there are already created iBGP Mesh MCMs that are not completed, so MUDA won't call again the ibpg_mesh.py
			if waiting_cr_mcm_completion:
				print(f"\n   There are iBGP Mesh MCMs previously created. Checking the status:")
				list_of_mcm = brick['mcm_ibgp_mesh'].split(",")
				for ibgp_mcm in list_of_mcm:
					cm_friendly_id = CmFriendlyIdentifier(friendly_id=ibgp_mcm)
					uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
					cm_status = uuid.cm.status_and_approvers.cm_status
					if cm_status  == 'Completed':
						cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
						print(f"   {ibgp_mcm} is Completed {cm_code}.")
					else:
						print(f"   {ibgp_mcm} is {cm_status}.")
						ibgp_mesh_mcm_incompleted.append(ibgp_mcm)

			print(f"\n   Checking device status in Jukebox:")
			list_of_devices = []	
			for device in devices_dx:
				if re.findall(r"-vc-car-|-vc-edg-",device):
					jb_data = jukebox.get_device_detail(device)
					if jb_data.data.device.device_state != 'in-service':
						print(f"   {device} is NOT in-service in JB, it requires iBGP Mesh MCM.")
						list_of_devices.append(device)
					else:
						print(f"   {device} is already in-service in JB, no iBGP Mesh MCM required.")

			if not list_of_devices:
				if "-br-agg-" not in devices_brick[0]:
					print("\n   All the VC-CAR devices are in-service, Deployment Completed")
				else:
					print("\n   All the VC-EDG devices are in-service, Deployment Completed")
				ddb_table_update(brick['brick'],38,False)

			ibgp_mesh_completed = True
			devices_missing_ibgp = []
			for device in list_of_devices:
				print(f"\n   Checking iBGP Mesh status on {device}")

				region = muda_auxiliary.get_dx_region(device)
				command = f"/apollo/env/NetengAutoChecks/bin/autochecks_manager --checks bgp.check_bgp_established_peers --target {device} --asns 16509,7224 --no-login-prompt --disable-snmp"
				command = f"ssh nebastion-{region.lower()} '{command}'"
				print(f"     {command}")
				try:
					output = subprocess.run(command, shell=True,stdout=PIPE, stderr=STDOUT)
					result = output.stdout.decode()
					check_result = re.findall(r"Check bgp.check_bgp_established_peers: ([A-Z]{4})",result)[0]
					print(f"   The Check result is: {check_result}")
					if check_result ==  "FAIL":
						neighbors_down = re.findall(r"([\d\.]+)\(remote-asn",result)
						print("   Checking if any BGP neighbors that are down are VC-CAR/CIR/EDG/RRR/AGG, ignoring BGP Expanders and Route Propagators, and ignoring devices NOT in-service.")

						config = hercules.get_latest_config_for_device(device,"released")
						config = config.decode().replace(' ', '')

						for neighbor in neighbors_down:
							pattern = "neighbor" + neighbor + "\{[\n\t]+description\"(.*)\""
							description = re.findall(pattern,config)
							if description:
								description = description[0]
								if re.findall(r"vc-car|vc-cir|vc-edg|vc-rrr|vc-agg",description):
									try:
										jb_data = jukebox.get_device_detail(description)
										jb_state = jb_data.data.device.device_state
									except:
										jb_state = "ERROR: not found"
											
									if jb_state != 'in-service':
										print(f"     {neighbor} - {description} - NOT in-service")
									else:
										print(f"     {neighbor} - {description} - in-service")
										ibgp_mesh_completed = False
										if device not in devices_missing_ibgp:
											devices_missing_ibgp.append(device)

				except Exception as e:
					print(f"ERROR: {e}")
					ibgp_mesh_completed = False
		
			if ibgp_mesh_completed:
				print("\nIBGP Mesh completed, moving to the next Step.")
				if "-br-agg-" not in devices_brick[0]:
					ddb_table_update(brick['brick'],32,False)#PoP Deployments have MMR Port Testing
				else:
					ddb_table_update(brick['brick'],33,False)#AZ Deployments don't have MMR Port Testing

			elif devices_missing_ibgp:
				print("\n\n   Some neighbors are in-service in Jukebox and the BGP is not Established with them.")
				print(f"   The following devices require iBGP Mesh MCM: {devices_missing_ibgp}")

				if ibgp_mesh_mcm_incompleted:
					print("\n   There are iBGP Mesh MCMs previously created but not Completed yet.")
					print("   Please complete the following MCMs: {}".format(", ".join(ibgp_mesh_mcm_incompleted)))

					print("\n   Updating MUDA step with list of pending MCMs.")
					ddb_table_update(brick['brick'],31,True,ibgp_mesh_mcm_incompleted)#Updating step with list of MCMs pending

				else:
					print("\n   Gathering parameters to call ibgp_mesh.py script")
					region = muda_auxiliary.get_dx_region(devices_missing_ibgp[0])
					command_bastion = f"ssh nebastion-{region.lower()} 'hostname'"
					print(f"\n   Looking for a Bastion in region {region.upper()}")
					try:
						output = subprocess.run(command_bastion, shell=True,stdout=PIPE, stderr=STDOUT)
						result = output.stdout.decode()
						neteng_bastion = re.findall(r"(neteng-bastion-.*.amazon.com)",result)[0]
						print(f"    Found {neteng_bastion}")

						print("\n   MUDA is running the iBGP Mesh script to create the MCMs:")
						command = "/apollo/env/DXDeploymentTools/bin/ibgp_mesh.py -nd {} -sb {}".format(",".join(devices_missing_ibgp),neteng_bastion)
						print(bcolors.lightcyan,command,bcolors.end)
						try:
							output = subprocess.run(command, shell=True,stdout=PIPE, stderr=STDOUT)
							result = output.stdout.decode()
							print(result)
							mcm_ids = re.findall(r"(MCM-[0-9]*) successfully updated",result)
							print("\n\n   ibgp_mesh.py has created the following MCMs: {}".format(", ".join(mcm_ids)))

							print("\n   Updating MUDA step with list of pending MCMs.")
							ddb_table_update(brick['brick'],31,True,mcm_ids)#Updating step with list of MCMs pending

						except:
							print("   ERROR: unable to create MCMs")

					except:
						print(f"    ERROR: unable to get neteng bastion for region {region}")

		##########################################################################################
		# 32 == MMR Port Testing
		elif int(brick['progress']) == 32:

			print(bcolors.lightcyan,"\n\n>> Complete the following manual tasks:",bcolors.end)
			print(bcolors.lightcyan,"\n    (a) MMR Port Testing:",bcolors.end,"make sure the MMR Port Testing is completed.")
			print("        Open",bcolors.lightcyan,f"https://w.amazon.com/bin/Wanwill/tools/PTTv2/WebHome",bcolors.end)

			print(bcolors.lightcyan,"\n    (b) REBASE VC-CAS:",bcolors.end,"when MMR Port Testing is done, provision the VC-CAS. The process is the same described on step (29).")

			print(bcolors.lightcyan,"\n    (c) START LOA VALIDATION:",bcolors.end,"start an email thread with the TPM, DCO and Colo (ask TPM to include Colo if you don't have the contact).")
			print("        Provide example from the columns 'Cage/Rack/PatchPanel/Port' from DCO cutsheet, and seek for Colo's validation on the format.")
			print("        LOA Validation is required for step (36) but it is not blocking you to move to the next step now.")

			answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
			if answer == "y":
				print("    Moving to the next step")
				ddb_table_update(brick['brick'],33,False)

		##########################################################################################
		# 33 == DX Side Control Plane Turn-UP
		elif int(brick['progress']) == 33:

			dx_devices = mcm.mcm_get_hostnames_from_regex(brick['dx'])
			brick_region = muda_auxiliary.get_border_region(brick['brick'])

			if "-br-agg-" in devices_brick[0]:
				deployment_type = "VC-BAR/EDG"
				deployment_type_nsm = "only VC-BAR "
				print(f"\n>> Step (33) is ready for its use with ClaymoreHD, but it was not tested yet.")
				print("   Please reach out to #muda-support to use this step on ClaymoreHD")
				break
			else:
				deployment_type = "VC-CAR/CAS/DAR"
				deployment_type_nsm = ""

			print(f"\n>> This step will move your {deployment_type} devices in JB 'APPROVED -> CONFIGURED -> IN-SERVICE', and {deployment_type_nsm}in NSM 'TURNED_UP -> OPERATIONAL'.")

			#print(f"Initial List of DX Devices: {dx_devices}")#VC-CAS not included
			new_dx_devices = []
			for device in dx_devices:
				new_dx_devices.append(device)
				for device_type in muda_data["vccas"]:
					if re.findall(device_type,device):
						stem = device.split("-r2")[0]
						stem = stem.replace("-vc-car-","-vc-cas-")
						for vccas in muda_data["vccas"][device_type]:
							new_dx_devices.append(stem+vccas)
			dx_devices = new_dx_devices			
			print(f"\n>> List of DX Devices: {dx_devices}")#Includes VC-CAS

			print("\n>> Getting JB and NSM status:")
			dx_devices_jb_approved = []
			dx_devices_jb_configured = []
			dx_devices_jb_inservice = []

			dx_devices_nsm_unknown = []
			dx_devices_nsm_turnedup = []
			dx_devices_nsm_operational = []
			
			for device in dx_devices:
				jb_data = jukebox.get_device_detail(device)
				print(f"{device}: JB status '{jb_data.data.device.device_state}'",end="")
				if jb_data.data.device.device_state == 'approved':
					dx_devices_jb_approved.append(device)
				elif jb_data.data.device.device_state == 'configured':
					dx_devices_jb_configured.append(device)
				elif jb_data.data.device.device_state == 'in-service':
					dx_devices_jb_inservice.append(device)

				nsm_info = nsm.get_devices_detail_from_nsm(device)
				nsm_status = 'UNKNOWN_STATUS'
				for info in nsm_info[0]+nsm_info[1]:
					if info.get('Name') == device:
						nsm_status = info.get('Life_Cycle_Status')
						break
				print(f", NSM status '{nsm_status}'")
				if nsm_status in ['OPERATIONAL','MAINTENANCE']:
					dx_devices_nsm_operational.append(device)
				elif nsm_status in ['TURNED_UP']:
					dx_devices_nsm_turnedup.append(device)
				else:
					dx_devices_nsm_unknown.append(device)

			print("\n>> JB status:")
			print(bcolors.lightcyan,"(1) JB APPROVED",bcolors.end,f"(will move to configured): {dx_devices_jb_approved}")
			print(bcolors.lightcyan,"(2) JB CONFIGURED",bcolors.end,f"(will move to in-service): {dx_devices_jb_configured}")
			print(bcolors.lightcyan,"(3) JB IN-SERVICE",bcolors.end,f"(final JB status, ready): {dx_devices_jb_inservice}")
			print("\n>> NSM status:")
			print(bcolors.lightcyan,"(4) NSM PRE-TURNED_UP",bcolors.end,f"(will move to turned_up): {dx_devices_nsm_unknown}")
			print(bcolors.lightcyan,"(5) NSM TURNED_UP",bcolors.end,f"(will move to operational): {dx_devices_nsm_turnedup}")
			print(bcolors.lightcyan,"(6) NSM OPERATIONAL",bcolors.end,f"(final NSM status, ready): {dx_devices_nsm_operational}")

			###If all devices are in-service in JB and operational in NSM this step is completed, for POP Deployments
			if dx_devices == dx_devices_jb_inservice and dx_devices == dx_devices_nsm_operational:
				print("\n\n>> All DX devices are 'in-service' in JB and 'operational' in NSM.")
				print("   Moving to the next Step.")
				ddb_table_update(brick['brick'],34,False)

			###If all devices are in-service in JB and VC-BAR Operational and VC-EDG Turn-Up in NSM this step is completed, for AZ Deployments
			if dx_devices == dx_devices_jb_inservice and dx_devices_nsm_operational == [x for x in dx_devices if "-vc-bar-" in x] and dx_devices_nsm_turnedup == [x for x in dx_devices if "-vc-edg-" in x]:
				print("\n\n>> All DX devices are 'in-service' in JB and VC-BAR 'operational' in NSM.")
				print("   Moving to the next Step.")
				ddb_table_update(brick['brick'],34,False)

			###If there are devices in JB APPROVED, we have to move them to CONFIGURED
			elif dx_devices_jb_approved:
				print(bcolors.lightcyan,"\n\n>> (1) Devices in JB APPROVED",bcolors.end,f"(will move to configured):\n    {dx_devices_jb_approved}.\n    Complete the following manual tasks:")
				print(bcolors.lightcyan,"\n    (a) OPEN TRACKING TT:",bcolors.end,"open a Tracking TT if you don't have one already.")
				print("        Clone",bcolors.lightcyan,"https://tt.amazon.com/0416534016",bcolors.end,f"for your {deployment_type} devices.")
				print(bcolors.lightcyan,"\n    (b) APPLY NARG:",bcolors.end,f"create NARGs for all your {deployment_type} devices, to avoid Sev2 on Turn-Up.")
				print("        Open",bcolors.lightcyan,"https://bladerunner.amazon.com/workflows/DX_NARG_Operations/versions/prod",bcolors.end)
				print(f"        Create one NARG Workflow per {deployment_type} device. Use your 'TrackingTT' and NARGACTION is 'apply'.")
				print(bcolors.lightcyan,"\n    (c) REVIEW SERIAL:",bcolors.end,f"the Serial Number in Jukebox for your {deployment_type} should be auto-populated already")
				print("        Review that the Serial Number in JB matches the one for your devices, or use the 'Fetch Actual Serial #' to populate it.")
				print("        If you had to populate the Serial Number, save the Edits, Submit for approval and get it approved.")	
				print(bcolors.lightcyan,"\n    (d) REVIEW NTP STATUS:",bcolors.end,f"Ensure NTP is working on all your {deployment_type} devices, to avoid Sev2 on Turn-Up.")
				print("        Use the NTP autocheck command from NOTES section of Step 33.")
				if "-br-agg-" in devices_brick[0]:
					print(bcolors.lightcyan,"\n    (e) AZ TURNUP VALIDATION:",bcolors.end,f"validate that it is safe to move the VC-EDG and VC-BAR to in-service, using the BRWF:")
					print("        https://bladerunner.amazon.com/workflows/AZ_DEVICE_TURNUP_VALIDATION/versions/prod")

				answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
				if answer == "y":
					print(f"    Moving devices in JB from APPROVED -> CONFIGURED: {dx_devices_jb_approved}")
					for device in dx_devices_jb_approved:
						print(f"    Updating Jukebox for {device}")
						try:
							jukebox.edit_device_state(device,'configured',muda_data["jukebox_approvers_l1"],muda_data["jukebox_approvers_l2"])
						except Exception as e:
							print(bcolors.red+f"    Error editing {device}: {e}"+bcolors.end)
					print("\n    Review and submit the edits (https://jukebox-web.corp.amazon.com/#/pendingEdits) and, when approved, run MUDA again.")
				else:
					print("\nTry it again later when those tasks are ready.")

			###If there are devices in JB CONFIGURED, we have to move them to IN-SERVICE
			elif dx_devices_jb_configured:
				print(bcolors.lightcyan,"\n\n>> (2) Devices in JB CONFIGURED",bcolors.end,f"(will move to in-service):")
				print(f"    Moving devices in JB from CONFIGURED -> IN-SERVICE: {dx_devices_jb_configured}")
				for device in dx_devices_jb_configured:
					print(f"    Updating Jukebox for {device}")
					try:
						jukebox.edit_device_state(device,'in-service',muda_data["jukebox_approvers"])
					except Exception as e:
						print(bcolors.red+f"    Error editing {device}: {e}"+bcolors.end)
				print("\n    Review and submit the edits (https://jukebox-web.corp.amazon.com/#/pendingEdits) and, when approved, run MUDA again.")

			###When all devices are IN-SERVICE in JB, if there are devices in NSM TURNED_UP, we have to move them to OPERATIONAL
			elif dx_devices_nsm_turnedup:
				print(bcolors.lightcyan,"\n\n>> (5) Devices in NSM TURNED_UP",bcolors.end,f"(will move to operational):\n    {dx_devices_nsm_turnedup}.\n    Complete the following manual tasks:")

				if "-br-agg-" in devices_brick[0]:
					dx_devices_nsm_turnedup = [x for x in dx_devices_nsm_turnedup if "-vc-bar-" in x]#Selects only VC-BAR to move to Operational
					print(bcolors.lightcyan,"\n    Only the VC-BAR are moved to OPERATINAL in this step.")
					print(bcolors.lightcyan,"    The VC-EDG are moved to OPERATINAL at the final deployment step, using the VC-EDG Turn-Up MCM.")
					answer = "y"

				else:
					device_site = dx_devices_nsm_turnedup[0].split("-")[0]
					print(bcolors.lightcyan,"\n    (a) ACTIVATE CERTIFICATES:",bcolors.end,"activate the certificates in Redfort.")
					print("        Open",bcolors.lightcyan,"https://redfort.amazon.com/",bcolors.end,f"and search for '{device_site}-vc-ca%' in the upper left search box.")
					print("        Open your Certificates and click 'ACTIVATE'.")
					print(bcolors.lightcyan,"\n    (b) ENABLE LOOPBACKS:",bcolors.end,"enable Loopbacks to Unshift the VC-CAR.")
					print("        Log into the VC-CAR devices with 'tt-mode' using your TrackingTT, like example: 'ssh joaq.tt.0307365415@iad53-vc-car-iad-r3'")
					print("        Confirm that Lo0.101 and Lo0.102 are disabled, and enable them:")
					print("           delete interfaces lo0.101 disable")
					print("           delete interfaces lo0.102 disable")
					answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"

				if answer == "y":
					print(f"    Moving devices in in NSM from TURNED_UP -> OPERATIONAL:\n    {dx_devices_nsm_turnedup}\n")
					tracking_tt = input("\n    Enter the Tracking TT number [0123456789]: ") or False
					if tracking_tt:
						for device in dx_devices_nsm_turnedup:
							nsm.update_state_nsm(device, "OPERATIONAL", tracking_tt, brick_region)
						print("    Run MUDA again to confirm status.")
					else:
						print("        No TrackingTT provided")

			##If there are devices in a PRE-TURNED_UP state, ask user to fix that issue.
			elif dx_devices_nsm_unknown:
				print(bcolors.lightcyan,"\n\n>> (4) Devices in NSM PRE-TURNED_UP",bcolors.end,f"(will move to turned_up):\n    {dx_devices_nsm_unknown}.")
				print("        This is an unexpected status, please read the instructions in MUDA Wiki Step (33) and make sure that your devices are TURNED_UP in NSM.")

			##Unexpected status
			else:
				print("ERROR: Unexpected status, please use #muda-support")

		##########################################################################################
		# 34 == Sostenuto Setup
		elif int(brick['progress']) == 34:

			print("\n    Follow the instructions in MUDA Wiki to complete the Sostenuto Setup for your AZ or PoP deployment:")

			answer = input("\n        Is the Sostenuto Setup completed? (y/n)? [n]: ") or "n"
			if answer == "y":
				print("        Moving to the next step")
				ddb_table_update(brick['brick'],35,False)

		##########################################################################################
		# 35 == Data Plane Turn-UP
		elif int(brick['progress']) == 35:

			dx_devices = mcm.mcm_get_hostnames_from_regex(brick['dx'])
			region_info = mcm.mcm_get_region_info()
			region = muda_auxiliary.get_dx_region(dx_devices[0])
			region_name = region_info[region]["name"]

			print(bcolors.lightcyan,"\n\n>> Complete the following manual tasks, more information in MUDA Wiki:",bcolors.end)

			print(bcolors.lightcyan,"\n    (a) ROUTE PROPAGATORS:",bcolors.end,"as part of the Sostenuto Step process, you have already Deployed DeviceList in Jukebox.")
			print("        That activates the Route Propagator Host BGP peering. Log into your VC-CAR devices and and confirm that with:")
			print("         > 'show configuration protocols bgp | display set | match aws-vpn-dx-' to show the IP of Route Propagators.")
			print("         > 'show bgp summary | match <RP_IP>' with each Route Propagator IP address, make sure they are Established.")
			print("        If they are not Established, follow the troubleshooting instructions in MUDA Wiki.")

			print(bcolors.lightcyan,"\n    (b) BGP EXPANDERS:",bcolors.end,"similarly, make sure the BGP Expanders neighborships are Established.")
			print("        If they are not, follow the instructions in MUDA Wiki, or open TT to DX Software to bounce them, example https://tt.amazon.com/0530199351.")


			print(bcolors.lightcyan,"\n    (c) UPDATE DASHBOARD:",bcolors.end,"add the devices to the Dashboards.")
			if "-br-agg-" not in devices_brick[0]:
				print("        Open",bcolors.lightcyan,f"https://w.amazon.com/bin/view/Harolotz/Dashboards/VC-CAR-Dashboard-{region.upper()}",bcolors.end,)
				print("        Click on 'Edit Source' on the top right of the wiki, and add the missing entries for your new devices.")
				for device in dx_devices:
					for device_type in muda_data["vccas"]:
						if re.findall(device_type,device):
							stem = device.split("-r2")[0]
							site = stem.split("-")[0]
							text = '{{transclude name="DXPOP2Router" ' + f'args="router1={stem}-r1|router2={stem}-r2|POP-Name={site.upper()}|region={region_name}' + '|LaunchStatus=Launched"/}}'
							print(f"\n           If there is already an entry with 'POP-Name={site.upper()}', add your devices there, changing the number in 'DXPOP?Router' with the number of devices. If your POP-Name is new, use:")
							print(bcolors.lightcyan,f"          {text}",bcolors.end)
				print("\n        Confirm that the new graphics are showing correct values.")
			else:
				print("        > Validate Carnival Monitoring: https://carnaval.amazon.com")
				print("        > Add to Premonition UI (opening TT) https://awsdashboard.amazon.com")
				print("        > Validate IXOps Dashboard https://w.amazon.com/index.php/Interconnect/Sostenuto/Dashboard")
				print("        > Add to SostenutoDxGwTgwDashboard")
				print("        > Add to SostenutoV2Dashboard")
				print("        > Add to SostenutoDxGwDashboard")


			print(bcolors.lightcyan,"\n    (d) REMOVE NARG:",bcolors.end,"remove NARGs for all your VC-CAR/CAS/DAR devices.")
			print("        Open",bcolors.lightcyan,"https://nretools.corp.amazon.com/oncall/",bcolors.end,"look for 'DX-OPS PRIMARY' and notify IXOps before doing this task.")
			print("        Open",bcolors.lightcyan,"https://bladerunner.amazon.com/workflows/DX_NARG_Operations/versions/prod",bcolors.end)
			print("        Create one NARG Workflow per VC-CAR/CAS/DAR device. Use your 'TrackingTT' and NARGACTION is 'remove'.")

			if "-br-agg-" not in devices_brick[0]:
				print(bcolors.lightcyan,"\n    (e) ENABLE DATAPLANE MONITORING:",bcolors.end,"enable DataPlane monitoring on VC-CAR/CAS (not on the VC-DAR).")
				print("        Open",bcolors.lightcyan,"https://nretools.corp.amazon.com/oncall/",bcolors.end,"look for 'DX-OPS PRIMARY' and notify IXOps before doing this task.")
				print("        Open",bcolors.lightcyan,"https://bladerunner.amazon.com/workflows/VeracityCLI/versions/prod",bcolors.end)
				print("        Create one NARG Workflow per VC-CAR/CAS (not on the VC-DAR) device. Use your 'TrackingTT' and OPERATION is 'enable_dataplane_monitoring'.")

			answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
			if answer == "y":
				print("   Moving to the next Step.")
				if "-br-agg-" not in devices_brick[0]:
					ddb_table_update(brick['brick'],36,False)
				else:
					print("New steps for VC-EDG Backfill MCM and VC-EDG Turn-Up MCM")

		##########################################################################################
		# 36 == Directconnectdashboard
		elif int(brick['progress']) == 36:

			list_of_devices = []
			if brick['dx'] != "None":
				print(bcolors.red,f"\n>> WARNING:",bcolors.end,"this step works for Cutsheets created with 'cutsheet_generator.py', populated by DCO, and uploaded to the Cutsheet MCM. If your Cutsheet was manually created, adjust the VC-CAS sheets to have the same column format the templates from 'cutsheet_generator.py' (more info https://w.amazon.com/bin/view/Interconnect/Tools/CutsheetGenerator/).")

				dx_devices = mcm.mcm_get_hostnames_from_regex(brick['dx'])
				phoenix_names = []
				for device in dx_devices:
					phoenix_name = re.findall(r"(.*-vc-car-.*-p.*-v.*-r)",device)
					if phoenix_name:
						phoenix_name_vccas = phoenix_name[0].replace("-vc-car-","-vc-cas-")
						if phoenix_name_vccas not in phoenix_names:
							phoenix_names.append(phoenix_name_vccas)

				if phoenix_names:
					cutsheets = brick['cutsheet_mcm'].split(",")
					listed_phoenix_names = ", ".join(phoenix_names)
					listed_cutsheets = ", ".join(cutsheets)
					print(f"\n   VC-CAS patterns to search in Cutsheet MCMs: {listed_phoenix_names}")
					print(f"   Cutsheet MCMs used on {brick['brick']}: {listed_cutsheets}")
					
					print("\n>> Is the",bcolors.lightcyan,"MMR Port Testing",bcolors.end,"completed, and your Cutsheet MCM updated with the MMR information provided by DCO",end="")
					answer = input(" (y/n)? [n]: ") or "n"
					if answer == "y":
						pwd = os.getcwd()
						location = input("\n Enter Location: ") or "MISSING_LOCATION"
						sublocation = input(" Enter Sublocation (or leave it blank): ") or ""

						print(f"\n>> Reading Cutsheet MCMs {cutsheets}:")
						peers,peers_vccas = muda_cutsheet.cutsheet_read_peers(cutsheets)
						files = []

						found_phoenix = []
						for phoenix_name in phoenix_names:
							print("\n>> Preparing CSV files for",bcolors.lightcyan,f"{phoenix_name.upper()}",bcolors.end)
							for vccas in peers_vccas:
								name_vccas = vccas.split(".")[0]
								if phoenix_name in vccas:
									file_path = "{}.csv".format(name_vccas)
									files.append(file_path)
									print(bcolors.lightcyan,f"\n>> VC-CAS CSV file {file_path}",bcolors.end)
									content = "hostname,interface_name,speed,cage,rack,patch_panel,ports,connector_type,location_code,sublocation_code\n"
									for line in peers_vccas[vccas]:
										content += f"{line},{location},{sublocation}\n"
									print(content)
									with open(file_path, 'w') as file:
										file.write(content)
									if phoenix_name not in found_phoenix:
										found_phoenix.append(phoenix_name)

						if files:
							print("\n\n>> List of CSV files:")
							for file in files:
								print(f"   {pwd}/{file}")

							username = user["username"]
							print("\n\n>> If your CSV files are correct, complete the next tasks:")
							
							print(bcolors.lightcyan,"\n    (a) UPLOAD PORTS:",bcolors.end,"open a new terminal to copy files to your Desktop with:")
							for phoenix_name in found_phoenix:
								print(f"        > scp {username}@{ncb}:{pwd}/{phoenix_name}* /Users/{username}/Desktop/.")
							print("        Drag and drop the files to",bcolors.lightcyan,"https://directconnectdashboard.corp.amazon.com/#/add_port_reservations",bcolors.end)
							print("        Confirm that the ports were added to DXDashboard and they are in 'TESTING' state. Do NOT change them to Available yet.")
							
							#print(bcolors.lightcyan,"\n    (b) LOA VALIDATION:",bcolors.end,"start an email thread with the TPM, DCO and Colo (ask TPM to include Colo if you don't have the contact).")
							#print("        Provide the following information and seek for Colo's validation on the format of the 'Cage/Rack/PatchPanel/Port'.")
							#for phoenix_name in found_phoenix:
							#	for vccas in peers_vccas:
							#		if phoenix_name in vccas:
							#			print("\n        > EXAMPLE for {}, interface {}, speed {}".format(line.split(",")[0],line.split(",")[1],line.split(",")[2]))
							#			print("          Cage: {}".format(line.split(",")[3]))
							#			print("          Rack: {}".format(line.split(",")[4]))
							#			print("          Patch Panel: {}".format(line.split(",")[5]))
							#			print("          Port: {}".format(line.split(",")[6]))
							#			break

							print(bcolors.lightcyan,"\n    (b) LOA VALIDATION:",bcolors.end,"schedule a call with ID/DCO team and COLO/Smart Hands technician to validate the LOA.")
							print("        Got to https://directconnectdashboard.corp.amazon.com/#/port_reservations, filter the output by your new devices and EXPORT that table into a new Cutsheet file.")
							print("        Smart Hands from the colo partner must validate this final Cutsheet with a physical audit of the information provided.")
							print("        When Smart Hands loops a port in the MMR, you must confirm that the rigth port in the right device comes up.")
							print("        It is not intended to test all the ports, since that was done in the MMR Port Testing, but just have a final confirmation from Smart Hands.")

							print(bcolors.lightcyan,"\n    (c) SERVICE PROVIDER:",bcolors.end,"if needed, add Service Provider to your Location: https://directconnectdashboard.corp.amazon.com/#/providers")
							print("        Ensure the public documentation for Providers is updated: https://aws.amazon.com/directconnect/partners/?nc=sn&loc=7&dn=1")
							print("        If needed, update Location Lat-Long information: https://code.amazon.com/packages/DirectConnectLocationLatLongs/blobs/mainline/--/index.js")

							answer = input("\n   Are the tasks above completed (y/n)? [n]: ") or "n"
							if answer == "y":
								print("   Moving to the next Step.")
								ddb_table_update(brick['brick'],37,False)
						else:
							print("\n\n>> Unable to read VC-CAS<>MMR information, please ask in #muda-support for assistance.")
				else:
					print(f"\n   Not found any Phoenix, Centennial or Heimdall to update in DXDashboard.")
					print("   Moving to the next Step.")
					ddb_table_update(brick['brick'],37,False)


		##########################################################################################
		# 40 == VC-EDG Backfill MCM
		elif int(brick['progress']) == 40:#Using new step number for testing, before re-ordering step numbers
			
			waiting_cr_mcm_completion = False

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['vc_edg_mcm'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				if cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						print(f"\n   {last_mcm} is Completed Successful, moving to the next step.")
						#ddb_table_update(brick['brick'],41,False)
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")

			#The CR/MCM was not created yet:
			else:
				print(f"        Devices BR: {devices_br}\n        Devices Brick: {devices_brick}\n        Devices DX: {devices_dx}\n")

				print("\nVC-EDG Backfill MCM is only needed if the same EdgGroup is active in another AZ")

				vcedg_devices = [x for x in devices_dx if "-vc-edg-" in x]
				print(f"\n>> VC-EDG devices: {vcedg_devices}")
				vcedg_devices_non_op = []
				for device in vcedg_devices:
					result = nsm.get_devices_from_nsm(device,state = ['OPERATIONAL','MAINTENANCE'])
					if device not in result:
						print(f"    {device} is NOT Operational in NSM.")
						vcedg_devices_non_op.append(device)
					else:
						print(f"    {device} is Operational in NSM.")
				if vcedg_devices_non_op:
					print(f"\n>> Non operational VC-EDG devices: {vcedg_devices_non_op}")
					vcedg_regex_non_op = muda_auxiliary.regex_from_list(vcedg_devices_non_op)
					print(f"   Regex: {vcedg_regex_non_op}")



				else:
					print("\nAll VC-EDG are operational. Nothing to do, moving to the last step")


		##########################################################################################
		# 41 == VC-EDG Turn-Up MCM
		elif int(brick['progress']) == 41:#Using new step number for testing, before re-ordering step numbers
			print("\nStep not ready")


		##########################################################################################
		# 37 == IXOps Handoff MCM creation
		elif int(brick['progress']) == 37:

			#Waiting for the CR/MCM approval/completion:
			if waiting_cr_mcm_completion:
				last_mcm = brick['mcm_ixops_handoff'].split(",")[-1]
				cm_friendly_id = CmFriendlyIdentifier(friendly_id=last_mcm)
				uuid = modeledcm.get_cm(GetCmRequest(None, cm_friendly_id))
				cm_status = uuid.cm.status_and_approvers.cm_status
				mcm_approved = False
				if cm_status  == 'Scheduled':
					mcm_approved = True
				elif cm_status  == 'Completed':
					cm_code = uuid.cm.status_and_approvers.closure_data.cm_closure_code
					if cm_code == 'Successful':
						mcm_approved = True
					else:
						print(f"\n   {last_mcm} is Completed, but {cm_code}.")
				else:
					print(f"\n   {last_mcm} is {cm_status}.")

				if mcm_approved:
					print(f"\n   {last_mcm} is {cm_status}.")

					print(bcolors.lightcyan,"\n    (a) FOR NEW POP:",bcolors.end,"if you deployed a new PoP, your Manager has to set it to 'Public' in DXDashboard: https://directconnectdashboard.corp.amazon.com/#/locations")
					print(bcolors.lightcyan,"\n    (b) AVAILABLE PORTS:",bcolors.end,"you have to manually 'Change Status' for the new customer ports to 'Available' in DXDashboard.")
					print("        EXCEPTION: all 100G ports (Centennial/Heimdall-100G) should remain in 'Testing' until GA, or unless otherwise directed by a NDM.")
					answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
					if answer == "y":
						print("\nMoving to the next step.")
						ddb_table_update(brick['brick'],38,False)

			#The CR/MCM was not created yet:
			else:
				print(bcolors.lightcyan,"\n\n>> Complete the following manual tasks:",bcolors.end)
				print(bcolors.lightcyan,"\n    (a) CHECK NSM:",bcolors.end,"check if your VC-CAR/CAS/DAR in NSM have the 'NOT_SHIFTED' tag.")
				print("        If you don't have the 'NOT_SHIFTED' tag, run the following command to generate it:")
				print("           /apollo/env/TrafficShift/bin/update_nsm.py --not-shifted --device <DEVICE_NAME>")

				print(bcolors.lightcyan,"\n    (b) DX LOCATION VERIFICATION:",bcolors.end,"run the DX Location Verification Workflow to make sure that your deployment is ready.")
				print("        Open",bcolors.lightcyan,"https://bladerunner.amazon.com/workflows/DX_Location_Verification/versions/prod",bcolors.end,)
				print("        Run it for each pair of VC-CAR and each pair of VC-DAR. All checks MUST pass, or IXOps won't take ownership of the devices.")
				print("        You could get the error 'The device is not in ConsoleDB', but you can check ConsoleDB and if it is there you can skip the check.")

				answer = input("\n    Are the tasks above completed (y/n)? [n]: ") or "n"
				if answer == "y":
					print(bcolors.lightcyan,"\n\n>> Creating IXOps Handoff MCM template.",bcolors.end)
				
					region = muda_auxiliary.get_dx_region(devices_dx[0])
					site = devices_dx[0].split("-")[0]
					sostenuto_validation = f"Sostenuto Dashboard:\nhttps://w.amazon.com/bin/view/Harolotz/Dashboards/VC-CAR-Dashboard-{region.upper()}/#H{site.upper()}\n"
					validation_links = []#In the future we can automate validations
				
					mcm_id,mcm_uuid,mcm_overview = mcm.mcm_creation("mcm_ixops_handoff",brick['dx'],sostenuto_validation,validation_links)
					print(f"        Created {mcm_id}.")
					steps = []
					steps.append({'title':f'Validate devices are ready for HandOff','time':30,'description':f'IXOps validation'})
					mcm.mcm_update(mcm_id,mcm_uuid,mcm_overview,steps)

					print(f"\nATTENTION: Review {mcm_id} and update the Overview with the 'Project SIM' and the 'DX_Location_Verification' result link")
					print("           Then, send it for approval and add it to the 'aws-ix-ops' Docket.")

					print("\nMoving to the next step.")
					ddb_table_update(brick['brick'],37,True,mcm_id)


		##########################################################################################
		# 38 == Deployment completed
		elif int(brick['progress']) == 38:

			print(f"\nThis deployment is completed.")
		



#############################################################################################################
##########################################  08. Update muda_table ###########################################
#############################################################################################################


#******************************************#
def ddb_table_update(brick,progress,*args):
	#brick/br/dx/progress/user/cutsheet_mcm/gb_cr/br_port_cr/br_port_mcm/br_pres_mcm/br_norm_cr/br_norm_mcm
	muda_table = ddb.get_ddb_table('muda_table')
	brick_from_table = ddb.get_device_from_table(muda_table,'brick',brick)
	now = datetime.datetime.now()
	time_now = now.strftime("%Y-%m-%d %H:%M")


	#Adding new BRICK
	if progress == 8:
		waiting_cr_mcm_completion = args[0]

		#When the Port Reservation CR is created
		if waiting_cr_mcm_completion:
			gb_cr = args[1]
			merge_command = args[2]
			if brick_from_table.get('gb_port_reservation_cr') != None:
				if gb_cr not in brick_from_table['gb_port_reservation_cr']:
					gb_cr = brick_from_table['gb_port_reservation_cr']+","+gb_cr
				else:
					gb_cr = brick_from_table['gb_port_reservation_cr']
			brick_from_table['gb_port_reservation_cr'] = gb_cr
			brick_from_table['merge_command'] = merge_command
			brick_from_table['port_reservation_nde'] = user["username"]
			last_cr = gb_cr.split(",")[-1]
			brick_from_table['comment'] = f"Port Reservation {last_cr} approval/merge."
			brick_from_table['time'] += "\n{} > Step ({}) by {} > {}".format(time_now,progress,user["username"],brick_from_table['comment'])
			brick_from_table['waiting_cr_mcm_completion'] = True
		
		#From 'new MCM' when a new deployment is created
		else:
			peers = args[1]
			loopbacks = args[2]
			ddb_br = args[3] # this is the regex of BR devices or ""
			ddb_dx = args[4] # this is the regex of DX devices or ""
			cutsheet_mcm = args[5]

			if ddb_br == "":
				ddb_br = "None"
			if ddb_dx == "":
				ddb_dx = "None"

			brick_list = mcm.mcm_get_hostnames_from_regex(brick)
			brick_loopbacks =  {}
			for device in brick_list:
				brick_loopbacks[device] = loopbacks.get(device)

			vccor_group = {}
			vccor_group[brick] = {}
			vccor_group[brick]["cor"] = []
			vccor_group[brick]["car"] = []
			vccor_group[brick]["kct"] = []
			vccor = brick.split("[")[0]
			for peer in peers:
				if vccor in peer.split("<>")[0]:
					if peer.split("<>")[0] not in vccor_group[brick]["cor"]:
						vccor_group[brick]["cor"].append(peer.split("<>")[0])
					mypeer = peer.split("<>")[1]

					if re.search(r"-br-kct-|-br-ctz-|-br-agg-",mypeer):
						if mypeer not in vccor_group[brick]["kct"]:
							vccor_group[brick]["kct"].append(mypeer)

					if re.search(r"-vc-car-|-vc-dar-|-vc-bar-|-vc-edg-|-vc-bdr-",mypeer):
						if mypeer not in vccor_group[brick]["car"]:
							vccor_group[brick]["car"].append(mypeer)


			original_dx_list = vccor_group[brick]["car"]
			for dx_secondary in original_dx_list:
				if re.search(r"-vc-dar-|-vc-bar-",dx_secondary):#Looking for devices under VC-BAR/DAR
					for peer in peers:
						if dx_secondary in peer.split("<>")[0]:
							mypeer = peer.split("<>")[1]
							if re.search(r"-vc-car-|-vc-edg-",mypeer):
								if mypeer not in vccor_group[brick]["car"]:
									vccor_group[brick]["car"].append(mypeer)

			brkctx = "None"
			vccarx = "None"
			if vccor_group[brick]["kct"] != []:
				brkctx = muda_auxiliary.regex_from_list(vccor_group[brick]["kct"])
			if vccor_group[brick]["car"] != []:
				vccarx = muda_auxiliary.regex_from_list(vccor_group[brick]["car"])

			#found = False
			#for cutsheet in user["cutsheets"]:
				#found = [x for x in user["cutsheets"][cutsheet]["devices"] if brick.split("[")[0] in x]
				#if found:
					#cutsheet_mcm = user["cutsheets"][cutsheet]["mcm"]

			if brick_from_table != None:
				initial_vccarx = brick_from_table['dx']
				initial_cutsheet = brick_from_table['cutsheet_mcm']

				if initial_vccarx != "None" and vccarx != "None":
					vccarx = vccarx.split("|")
					vccarx = [x for x in vccarx if x not in initial_vccarx]
					if vccarx:
						vccarx = initial_vccarx+"|"+"|".join(vccarx)
					else:
						vccarx = initial_vccarx
				elif vccarx == "None":
					vccarx = initial_vccarx

				if cutsheet_mcm not in initial_cutsheet:
					cutsheet_mcm = initial_cutsheet+","+cutsheet_mcm
				else:
					cutsheet_mcm = initial_cutsheet

				brick_from_table['progress']= progress
				brick_from_table['dx']= vccarx
				brick_from_table['cutsheet_mcm']= cutsheet_mcm
				brick_from_table['brick_loopbacks']= brick_loopbacks
				brick_from_table['peers']= peers
				brick_from_table['loopbacks']= loopbacks
				brick_from_table['comment'] = "Port Reservation CR creation."
				brick_from_table['time'] += "\n{} > Step ({}) by {} > {}".format(time_now,progress,user["username"],brick_from_table['comment'])

			else:
				brick_from_table = {'brick': brick, 'br' : ddb_br,'dx': ddb_dx,'progress':progress,'cutsheet_mcm':cutsheet_mcm,'brick_loopbacks':brick_loopbacks,'peers':peers,'loopbacks':loopbacks}
				brick_from_table['comment'] = "Port Reservation CR creation."
				brick_from_table['time'] = "{} > Step ({}) by {} > {}".format(time_now,progress,user["username"],brick_from_table['comment'])
		
			brick_from_table['lead'] = user["username"]
			brick_from_table['waiting_cr_mcm_completion'] = False
		
		#print(">> Creating DDB entry: {}".format(brick_from_table))
		response = ddb.put_item_to_table(muda_table,brick_from_table)

	#MOVING BRRICK TO SPECIFIC NUMBER
	elif brick_from_table != None:
		waiting_cr_mcm_completion = args[0]
		brick_from_table['waiting_cr_mcm_completion'] = waiting_cr_mcm_completion

		if progress == 9:
			#When the Port Reservation MCM is created
			if waiting_cr_mcm_completion:
				mcm_port_reservation = args[1]
				if brick_from_table.get('gb_port_reservation_mcm') != None:
					if mcm_port_reservation not in brick_from_table['gb_port_reservation_mcm']:
						mcm_port_reservation = brick_from_table['gb_port_reservation_mcm']+","+mcm_port_reservation
					else:
						mcm_port_reservation = brick_from_table['gb_port_reservation_mcm']
				brick_from_table['gb_port_reservation_mcm'] = mcm_port_reservation
				last_mcm = mcm_port_reservation.split(",")[-1]
				brick_from_table['comment'] = f"Port Reservation {last_mcm} approval/deploy."
			#When the Port Reservation MCM is not created
			else:
				brick_from_table['comment'] = "Port Reservation MCM creation."

		if progress == 10:
			brick_from_table['comment'] = "Conditional Manual Tasks."

		if progress == 11:
			brick_from_table['comment'] = "Create Jukebox Devices, Cabling and Links."

		if progress == 12:
			#When the Port Reservation CR is created
			if waiting_cr_mcm_completion:
				mcm_port_reservation = args[1]
				ports_to_shutdown = args[2]
				if brick_from_table.get('dx_port_reservation_mcm') != None:
					if mcm_port_reservation not in brick_from_table['dx_port_reservation_mcm']:
						mcm_port_reservation = brick_from_table['dx_port_reservation_mcm']+","+mcm_port_reservation
					else:
						mcm_port_reservation = brick_from_table['dx_port_reservation_mcm']
				brick_from_table['dx_port_reservation_mcm'] = mcm_port_reservation
				last_mcm = mcm_port_reservation.split(",")[-1]
				brick_from_table['ports_to_shutdown'] = ports_to_shutdown
				brick_from_table['comment'] = f"DX side Port Reservation {last_mcm} approval/deploy."
			#When the Port Reservation MCM is not created
			else:
				peers = args[1]
				loopbacks = args[2]
				brick_from_table['comment'] = "DX side Port Reservation MCM creation."
				brick_from_table['peers']= peers
				brick_from_table['loopbacks']= loopbacks

		if progress == 13:
			brick_from_table['comment'] = "Scaling Port testing Mobius."

		if progress == 14:
			#When the Port Reservation MCM is created
			if waiting_cr_mcm_completion:
				port_shutdown_mcm = args[1]
				if brick_from_table.get('port_shutdown_mcm') != None:
					if port_shutdown_mcm not in brick_from_table['port_shutdown_mcm']:
						port_shutdown_mcm = brick_from_table['port_shutdown_mcm']+","+port_shutdown_mcm
					else:
						port_shutdown_mcm = brick_from_table['port_shutdown_mcm']
				brick_from_table['port_shutdown_mcm'] = port_shutdown_mcm
				last_mcm = port_shutdown_mcm.split(",")[-1]
				brick_from_table['comment'] = f"Scaling Port Shutdown {last_mcm} approval/deploy."
			#When the Port Reservation MCM is not created
			else:
				brick_from_table['comment'] = "Scaling Port Shutdown MCM creation."

		if progress == 15:
			#When the Port Reservation MCM is created
			if waiting_cr_mcm_completion:
				mcm_aclmanage = args[1]
				if brick_from_table.get('mcm_aclmanage') != None:
					if mcm_aclmanage not in brick_from_table['mcm_aclmanage']:
						mcm_aclmanage = brick_from_table['mcm_aclmanage']+","+mcm_aclmanage
					else:
						mcm_aclmanage = brick_from_table['mcm_aclmanage']
				brick_from_table['mcm_aclmanage'] = mcm_aclmanage
				last_mcm = mcm_aclmanage.split(",")[-1]
				brick_from_table['comment'] = f"ACLManage {last_mcm} approval/deploy."
			#When the Port Reservation MCM is not created
			else:
				peers = args[1]
				loopbacks = args[2]
				brick_from_table['peers']= peers
				brick_from_table['loopbacks']= loopbacks
				brick_from_table['comment'] = "ACLManage MCM before BGP Prestage, creation."

		if progress == 16:
			#When the Port Reservation CR is created
			if waiting_cr_mcm_completion:
				gb_cr = args[1]
				merge_command = args[2]
				release_command = args[3]
				tiedown = args[4]
				if brick_from_table.get('gb_cr') != None:
					if gb_cr not in brick_from_table['gb_cr']:
						gb_cr = brick_from_table['gb_cr']+","+gb_cr
					else:
						gb_cr = brick_from_table['gb_cr']
				if tiedown != {}:
					brick_from_table['tiedown'] = tiedown
				brick_from_table['gb_cr'] = gb_cr
				brick_from_table['merge_command'] = merge_command
				brick_from_table['release_command'] = release_command
				last_cr = gb_cr.split(",")[-1]
				brick_from_table['comment'] = f"GenevaBuilder Brick attributes {last_cr} approval/merge."
			#When the Port Reservation MCM is not created
			else:
				peers = args[1]
				loopbacks = args[2]
				brick_from_table['comment'] = "GenevaBuilder Brick attributes CR creation."
				brick_from_table['peers']= peers
				brick_from_table['loopbacks']= loopbacks

		if progress == 17:
			#When waiting for Release configs:
			if waiting_cr_mcm_completion:
				#If staying in the same progress, updating table with pending Border devices prestage
				if brick_from_table.get('br_prestage') != None:
					br_prestage = brick_from_table['br_prestage']
				else:
					br_prestage = {}
					br_prestage["released"] = {}
					br_prestage["released"]["done"] = []
					br_prestage["released"]["missing"] = []
					br_prestage["collected"] = {}
					br_prestage["collected"]["done"] = []
					br_prestage["collected"]["missing"] = []

				try:#if there is Border prestage info, update
					br_prestage_done = args[1]
					br_prestage_missing = args[2]

					br_prestage["collected"]["done"] = br_prestage_done
					br_prestage["collected"]["missing"] = br_prestage_missing
					missing = str(len(br_prestage["collected"]["missing"]))
					total = str(len(br_prestage["collected"]["missing"]) + len(br_prestage["collected"]["done"]))

					try:#If there is MCM information, update
						manualpcn = args[3]
						if brick_from_table.get('manualpcn') != None:
							if manualpcn not in brick_from_table['manualpcn']:
								manualpcn = brick_from_table['manualpcn']+","+manualpcn
							else:
								manualpcn = brick_from_table['manualpcn']
						brick_from_table['manualpcn'] = manualpcn
						brick_from_table['comment'] = f"Border prestage config missing in {missing} out of {total} devices and ManualPCN {manualpcn}"
					except:
						if brick_from_table.get('manualpcn') != None:
							manualpcn = brick_from_table['manualpcn']
							brick_from_table['comment'] = f"Border prestage config missing in {missing} out of {total} devices and ManualPCN {manualpcn}"
						else:
							brick_from_table['comment'] = f"Border prestage config missing in {missing} out of {total} devices."
				except:
					brick_from_table['comment'] = f"Border prestage configs."

			#When waiting for Prestage configs:
			else:
				brick_from_table['comment'] = "Border release configs."

		if progress == 18:
			brick_from_table['comment'] = "VC-COR console, software and cabling validation."

		if progress == 19:
			#When the Port Reservation CR is created
			if waiting_cr_mcm_completion:
				gb_cr = args[1]
				merge_command = args[2]
				release_command = args[3]
				tiedown = args[4]
				if brick_from_table.get('gb_cr') != None:
					if gb_cr not in brick_from_table['gb_cr']:
						gb_cr = brick_from_table['gb_cr']+","+gb_cr
					else:
						gb_cr = brick_from_table['gb_cr']
				if tiedown != {}:
					brick_from_table['tiedown'] = tiedown
				brick_from_table['gb_cr'] = gb_cr
				brick_from_table['merge_command'] = merge_command
				brick_from_table['release_command'] = release_command
				last_cr = gb_cr.split(",")[-1]
				brick_from_table['comment'] = f"GenevaBuilder LAG attribute {last_cr} approval/merge."
			#When the Port Reservation MCM is not created
			else:
				brick_from_table['comment'] = "GenevaBuilder LAG attribute CR creation."


		if progress == 20:
			brick_from_table['comment'] = "Brick provisioning."

		if progress == 21:
			brick_from_table['comment'] = "Mobius testing."

		if progress == 22:
			#When the MCM is created
			if waiting_cr_mcm_completion:
				mcm_prestage = args[1]
				if brick_from_table.get('mcm_border_prestage') != None:
					if mcm_prestage not in brick_from_table['mcm_border_prestage']:
						mcm_prestage = brick_from_table['mcm_border_prestage']+","+mcm_prestage
					else:
						mcm_prestage = brick_from_table['mcm_border_prestage']
				brick_from_table['mcm_border_prestage'] = mcm_prestage
				last_mcm = mcm_prestage.split(",")[-1]
				brick_from_table['comment'] = f"Border/Brick Prestage {last_mcm} approval/deploy."
				try:
					lags_to_prestage = args[2]
					brick_from_table['lags_to_prestage'] = lags_to_prestage#replaces existing lags
				except:
					pass

			#When the MCM is not created
			else:
				brick_from_table['comment'] = "Border/Brick Prestage MCM creation."
				try:
					mobius_link = args[1]
					if brick_from_table.get('mobius_link') != None:
						if mobius_link not in brick_from_table['mobius_link']:
							mobius_link = brick_from_table['mobius_link']+","+mobius_link
						else:
							mobius_link = brick_from_table['mobius_link']
					brick_from_table['mobius_link'] = mobius_link
				except:
					pass
			
		if progress == 23:
			#When the Port Reservation MCM is created
			if waiting_cr_mcm_completion:
				mcm_aclmanage = args[1]
				if brick_from_table.get('mcm_aclmanage') != None:
					if mcm_aclmanage not in brick_from_table['mcm_aclmanage']:
						mcm_aclmanage = brick_from_table['mcm_aclmanage']+","+mcm_aclmanage
					else:
						mcm_aclmanage = brick_from_table['mcm_aclmanage']
				brick_from_table['mcm_aclmanage'] = mcm_aclmanage
				last_mcm = mcm_aclmanage.split(",")[-1]
				brick_from_table['comment'] = f"ACLManage {last_mcm} approval/deploy."
			#When the Port Reservation MCM is not created
			else:
				brick_from_table['comment'] = "ACLManage MCM after BGP Prestage, creation."

		if progress == 24:
			brick_from_table['comment'] = "SLAX and Herbie prevalidation."

		if progress == 25:
			#When the Port Reservation MCM is created
			if waiting_cr_mcm_completion:
				gb_cr = args[1]
				merge_command = args[2]
				if brick_from_table.get('gb_port_normalization_cr') != None:
					if gb_cr not in brick_from_table['gb_port_normalization_cr']:
						gb_cr = brick_from_table['gb_port_normalization_cr']+","+gb_cr
					else:
						gb_cr = brick_from_table['gb_port_normalization_cr']
				brick_from_table['gb_port_normalization_cr'] = gb_cr
				brick_from_table['merge_command'] = merge_command

				last_cr = gb_cr.split(",")[-1]
				brick_from_table['comment'] = f"BR-KCT Normalization {last_cr} approval/merge."
			#When the Port Reservation MCM is not created
			else:
				brick_from_table['comment'] = "BR-KCT Normalization CR creation."

		if progress == 26:
			#When the MCM is created
			if waiting_cr_mcm_completion:
				mcm_normalization = args[1]
				lags_to_prestage = args[2]
				if brick_from_table.get('mcm_border_normalization') != None:
					if mcm_normalization not in brick_from_table['mcm_border_normalization']:
						mcm_normalization = brick_from_table['mcm_border_normalization']+","+mcm_normalization
					else:
						mcm_normalization = brick_from_table['mcm_border_normalization']
				brick_from_table['mcm_border_normalization'] = mcm_normalization
				brick_from_table['lags_to_prestage'] = lags_to_prestage#replaces existing lags
				last_mcm = mcm_normalization.split(",")[-1]
				brick_from_table['comment'] = f"BR-KCT Normalization {last_mcm} approval/deploy."
			#When the MCM is not created
			else:
				brick_from_table['comment'] = "BR-KCT Normalization MCM creation."

		if progress == 27:#The handoff MCM will be handled in step 27
			brick_from_table['comment'] = "VC-COR Brick Handover to IXOps."

		if progress == 28:#The handoff MCM will be handled in step 27
			#mcm_ixops_handoff = args[0]
			#if brick_from_table.get('mcm_ixops_handoff') != None:
			#	if mcm_ixops_handoff not in brick_from_table['mcm_ixops_handoff']:
			#		mcm_ixops_handoff = brick_from_table['mcm_ixops_handoff']+","+mcm_ixops_handoff
			#	else:
			#		mcm_ixops_handoff = brick_from_table['mcm_ixops_handoff']
			#brick_from_table['mcm_ixops_handoff'] = mcm_ixops_handoff
			#last_mcm = mcm_ixops_handoff.split(",")[-1]
			#brick_from_table['comment'] = f"IXOps Handoff {last_mcm} approval."
			brick_from_table['comment'] = "Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD console, software and cabling validation."

		if progress == 29:
			brick_from_table['comment'] = "Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD provisioning."

		if progress == 30:
			brick_from_table['comment'] = "Phoenix/Centennial/Heimdall/VC-DAR/ClaymoreHD Mobius testing."

		if progress == 31:
			#When the MCM is created
			if waiting_cr_mcm_completion:
				mcm_ibgp_mesh_list = args[1]
				if brick_from_table.get('mcm_ibgp_mesh') != None:
					mcm_ibgp_mesh_in_table = brick_from_table['mcm_ibgp_mesh']
					for mcm_ibgp_mesh in mcm_ibgp_mesh_list:
						if mcm_ibgp_mesh not in mcm_ibgp_mesh_in_table:
							mcm_ibgp_mesh_in_table = mcm_ibgp_mesh_in_table+","+mcm_ibgp_mesh
				else:
					mcm_ibgp_mesh_in_table = ",".join(mcm_ibgp_mesh_list)

				brick_from_table['mcm_ibgp_mesh'] = mcm_ibgp_mesh_in_table
				list_last_mcms = ",".join(mcm_ibgp_mesh_list)
				brick_from_table['comment'] = f"IBGP Mesh MCMs {list_last_mcms} approval/deploy."
			#When the MCM is not created
			else:
				brick_from_table['comment'] = "IBGP Mesh MCMs creation."

		if progress == 32:
			brick_from_table['comment'] = "MMR Port Testing."

		if progress == 33:
			brick_from_table['comment'] = "Control Plane Turn-up."

		if progress == 34:
			brick_from_table['comment'] = "Sostenuto Setup."

		if progress == 35:
			brick_from_table['comment'] = "Data Plane Turn-Up."

		if progress == 36:
			brick_from_table['comment'] = "LOA Validation and DXDashboard."

		if progress == 37:
			#When the MCM is created
			if waiting_cr_mcm_completion:
				mcm_ixops_handoff = args[1]
				if brick_from_table.get('mcm_ixops_handoff') != None:
					if mcm_ixops_handoff not in brick_from_table['mcm_ixops_handoff']:
						mcm_ixops_handoff = brick_from_table['mcm_ixops_handoff']+","+mcm_ixops_handoff
					else:
						mcm_ixops_handoff = brick_from_table['mcm_ixops_handoff']
				brick_from_table['mcm_ixops_handoff'] = mcm_ixops_handoff
				last_mcm = mcm_ixops_handoff.split(",")[-1]
				brick_from_table['comment'] = f"IXOps Handoff {last_mcm} approval."
			#When the MCM is not created
			else:
				brick_from_table['comment'] = "IXOps Handoff MCM creation."

		if progress == 38:
			brick_from_table['comment'] = "Deployment completed."

		brick_from_table['progress'] = progress
		brick_from_table['time'] += "\n{} > Step ({}) by {} > {}".format(time_now,progress,user["username"],brick_from_table['comment'])

		response = ddb.put_item_to_table(muda_table,brick_from_table)

	return



#############################################################################################################
##########################################  08. Prompt and Main #############################################
#############################################################################################################

#******************************************#
class MyPrompt(Cmd):
	intro = bcolors.orange + ">> Welcome to MUDA\n\n   Wiki: https://w.amazon.com/bin/view/DXDEPLOY/Runbooks/MUDA/\n   Deployments: https://dxdeploymenttools.corp.amazon.com/muda\n   Slax support channel: #muda-support\n\n"
	prompt = bcolors.orange + "(muda)> "

	def __init__(self,possible_bricks):
		Cmd.__init__(self)
		self.possible_bricks = possible_bricks

	def do_new(self,args):
		"""New cutsheet for VC-COR deployment"""
		print(bcolors.end)
		cutsheets = []
		vccors = []
		vccars = []
		brkcts = []
		devicex = []
		peers = {}
		loopbacks = {}
		created_files = {}
		tiedown = {}

		command_list = args.split()
		if len(command_list) == 1:
			mcm_string = command_list[0]
			if re.search(r"^MCM-\d+$",mcm_string):
				print(f"\n>> Reading Cutsheet {mcm_string}")
				cutsheets = [mcm_string]
				peers,peers_vccas = muda_cutsheet.cutsheet_read_peers(cutsheets)

				#for vccas in peers_vccas:
				#	print(f"\n>> VC-CAS CSV file for DXDashboard ports in {vccas}")
				#	for line in peers_vccas[vccas]:
				#		print(f"{line}")

				ddb_brick,ddb_br,ddb_dx,peers,loopbacks = muda_dogfish.dogfish_read_ip(peers,peers_vccas,loopbacks,bgp_communities,True)#does DNS check

				list_second_level = []
				if ddb_brick == []:
					for peer in peers:
						parent_device = peer.split("<>")[0]
						if re.findall(r"-vc-dar-|-vc-bar-",parent_device):
							if parent_device not in list_second_level:
								list_second_level.append(parent_device)
					if list_second_level:
						list_second_level.sort()
						regex_second_level = muda_auxiliary.regex_from_list(list_second_level)
						print(f"\n>> There is no Brick name on the cutsheet.\n   Found second layer devices (VC-DAR/BAR): {regex_second_level}.\n   Looking for the brick.")
						muda_table = ddb.get_ddb_table('muda_table')
						muda_dict = ddb.scan_full_table(muda_table)
						brick_read = [x['brick'] for x in muda_dict if regex_second_level in x['dx']]
						group_brick_read = "|".join(brick_read)
						print(f"   Found parent Bricks: {group_brick_read}")
						ddb_brick = mcm.mcm_get_hostnames_from_regex(group_brick_read)

				if ddb_brick != []:
					bricks = muda_auxiliary.regex_from_list_ignore_missing(ddb_brick).split("|")
					ddb_br = muda_auxiliary.regex_from_list(ddb_br)
					ddb_dx = muda_auxiliary.regex_from_list(ddb_dx)
					for brick in bricks:
						print(f"\n>> Creating DynamoDB entry for for: {brick}, BR {ddb_br}, DX {ddb_dx}")
						ddb_table_update(brick,8,False,peers,loopbacks,ddb_br,ddb_dx,mcm_string) # waiting_cr_mcm_completion is False

					list_of_cutsheets = []
					for brick in bricks:
						muda_table = ddb.get_ddb_table('muda_table')
						muda_dict = ddb.scan_full_table(muda_table)
						brick_read = [x for x in muda_dict if brick == x['brick']][0]
						list_of_cutsheets += brick_read['cutsheet_mcm'].split(",")

					list_of_cutsheets = list(dict.fromkeys(list_of_cutsheets))
					user["mcm_list"] = list_of_cutsheets	
					if len(user["mcm_list"]) > 1:#There were previous cutsheets, reading them to update loopbacks and peers:
						mcm_listed = user["mcm_list"]
						print(f"\n\n>> MUDA detected Cutsheets related to bricks {bricks}, reading all of them: {mcm_listed}")
						peers = {}
						loopbacks = {}
									
						cutsheets = user["mcm_list"]
						peers,peers_vccas = muda_cutsheet.cutsheet_read_peers(cutsheets)

						ddb_brick_discard,ddb_br_discard,ddb_dx_new,peers,loopbacks = muda_dogfish.dogfish_read_ip(peers,peers_vccas,loopbacks,bgp_communities,False)#no DNS check
						for brick in bricks:
							print(f"\n>> Updating DynamoDB for: {brick}, BR {ddb_br}, DX {ddb_dx_new}")
							ddb_table_update(brick,8,False,peers,loopbacks,ddb_br,ddb_dx_new,mcm_string)#add possible nested devices (VC-CAR behind VC-DAR) but not more parents (BR). waiting_cr_mcm_completion is False

					else:
						print(f"\n>> There are no previous Cutsheets related to bricks {bricks}.")

			else:
				print("      Please use 'new MCM-00000000'\n")
		else:
			print("      Please use 'new MCM-00000000'\n")

	def do_dxdb(self,args):
		"""Creates CSV file for DXDashboard"""
		print(bcolors.end)
		command_list = args.split()
		if len(command_list) == 1:
			mcm_string = command_list[0]
			if re.search(r"^MCM-\d+$",mcm_string):
				print(f"\n>> Reading Cutsheet {mcm_string}")
				cutsheets = [mcm_string]
				peers,peers_vccas = muda_cutsheet.cutsheet_read_peers(cutsheets)

				pwd = os.getcwd()
				location = input("\n Enter Location: ") or "MISSING_LOCATION"
				sublocation = input(" Enter Sublocation (or leave it blank): ") or ""
				files = []

				for vccas in peers_vccas:
					print(f"\n>> VC-CAS CSV file for DXDashboard ports in {vccas}")
					name_vccas = vccas.split(".")[0]
					file_path = "{}.csv".format(name_vccas)
					files.append(file_path)
					print(bcolors.lightcyan,f"\n>> VC-CAS CSV file {file_path}",bcolors.end)

					content = "hostname,interface_name,speed,cage,rack,patch_panel,ports,connector_type,location_code,sublocation_code\n"
					for line in peers_vccas[vccas]:
						content += f"{line},{location},{sublocation}\n"
					print(content)
					with open(file_path, 'w') as file:
						file.write(content)

				if files:
					print("\n\n>> List of CSV files:")
					for file in files:
						print(f"   {pwd}/{file}")


			else:
				print("      Please use 'dxdb MCM-00000000'\n")
		else:
			print("      Please use 'dxdb MCM-00000000'\n")

	def do_auto(self,possible_bricks):
		"""Automatically moves deployment to the next step"""
		print(bcolors.end)
		if len(possible_bricks) < 11:
			print("Please use a more specific Brick name. Example 'sea4-vc-cor-b1'.")
			#muda_auto("",peers,vccors,loopbacks,df,bgp_communities,modeledcm)
		else:
			muda_auto(possible_bricks,peers,vccors,loopbacks,df,bgp_communities,modeledcm)
		print()

	def do_show(self,possible_bricks):
		"""Shows deployments and their status"""
		print(bcolors.end)
		if len(possible_bricks) == 0:
			muda_show("")
		else:
			muda_show(possible_bricks)
		print()

	def do_log(self,possible_bricks):
		"""Shows deployments and their status"""
		print(bcolors.end)
		if len(possible_bricks) == 0:
			muda_log("")
		else:
			muda_log(possible_bricks)
		print()

	def do_stats(self,possible_bricks):
		"""Shows deployments and their status"""
		print(bcolors.end)
		muda_stats()
		print()

	def completedefault(self, text, line, begidx, endidx):
		tokens = line.split()
		if tokens[0].strip() == "show" or tokens[0].strip() == "auto":
			return self.possible_bricks_matches(text)
		return []

	def possible_bricks_matches(self, text):
		matches = []
		n = len(text)
		for word in self.possible_bricks:
			if word[:n] == text:
				 matches.append(word)
		return matches

	def do_update(self,args):
		"""Updates Border Customer Space prefix list"""
		print(bcolors.end)
		cs_prefixes = df.dogfish_find_customer_space("PublicIP",muda_data["regions"])
		#cs_prefixes = df.dogfish_find_customer_space("PublicIP",["pdx"])

		print("\n>> Updating border_customer_space.")
		muda_var = ddb.get_ddb_table('muda_var')
		muda_variable = {"var":"border_customer_space","content":cs_prefixes}
		response = ddb.put_item_to_table(muda_var,muda_variable)

		muda_var_dx_infra_space = {}
		muda_var_border_infra_space = {}
		muda_var_border_unlabeled_space = {}
		muda_var_telesto_compute_space = {}
		regions = [x.upper() for x in muda_data["regions"]]

		for region in regions:
			muda_var_dx_infra_space[region] = muda_data["dogfish_allocations"]["dx_infra_range"]["any"]
			muda_var_border_unlabeled_space[region] = muda_data["dogfish_allocations"]["unlabeled_range"]["any"]
			muda_var_telesto_compute_space[region] = muda_data["dogfish_allocations"]["infra_compute_range"]["any"]
			if region == "BJS":
				muda_var_border_infra_space[region] = muda_data["dogfish_allocations"]["border_infra_range"]["bjs"]
			elif region == "ZHY":
				muda_var_border_infra_space[region] = muda_data["dogfish_allocations"]["border_infra_range"]["zhy"]
			else:
				muda_var_border_infra_space[region] = muda_data["dogfish_allocations"]["border_infra_range"]["any"]

		print(">> Updating dx_infra_space.")
		muda_variable = {"var":"dx_infra_space","content":muda_var_dx_infra_space}
		response = ddb.put_item_to_table(muda_var,muda_variable)
		print(">> Updating border_infra_space.")
		muda_variable = {"var":"border_infra_space","content":muda_var_border_infra_space}
		response = ddb.put_item_to_table(muda_var,muda_variable)
		print(">> Updating border_unlabeled_space.\n")
		muda_variable = {"var":"border_unlabeled_space","content":muda_var_border_unlabeled_space}
		response = ddb.put_item_to_table(muda_var,muda_variable)
		print(">> Updating telesto_compute_space.\n")
		muda_variable = {"var":"telesto_compute_space","content":muda_var_telesto_compute_space}
		response = ddb.put_item_to_table(muda_var,muda_variable)

	def do_dogfish(self,args):
		"""Dogfish IP allocation"""
		global dogfish_material_set

		print(bcolors.end)
		command_list = args.split()

		if command_list == []:
			print(""">> Change the default material set:
dogfish com.amazon.credentials.isengard.894712427633.user/dx-deploy-df-user
\n>> Provision Loopbacks (/32) prefixes:
dogfish loop PublicIP 150.222.222.0/32 sfo5-vc-cor-b1-r1 Primary Gray
dogfish loop PublicIP 150.222.222.0/32 sfo5-vc-cor-b1-r1 Unlabeled Loopback
\n>> Provision P2P (/32) prefixes:
dogfish p2p PublicIP 150.222.222.2/31 sfo5-vc-cor-b1-r1 sfo5-br-kct-p1-r1 P2P
dogfish p2p PublicIP 150.222.222.2/31 sfo5-vc-cor-b1-r1 sfo5-br-kct-p1-r1 CSC
dogfish p2p PublicIP 150.222.222.2/31 sfo5-vc-cor-b1-r1 sfo5-br-kct-p1-r1 Internet
\n>> Provision Sostenuto (/30) prefixes:
dogfish sostenuto IAD_DX 52.119.201.116/30 iad53-vc-car-r1
\n>> Delete prefixes:
dogfish delete BORDER_FABRICS 100.103.242.160/31
			""")

		if len(command_list) == 1:
			dogfish_material_set = command_list[0]
			print(f">> Updated Dogfish Material Set: {dogfish_material_set}\n")
		else:
			print(f">> Current Dogfish Material Set: {dogfish_material_set}\n")
			try:
				dfish = dogfish.DogFish(dogfish_material_set,True)
			except:
				print(f"Material set not supported: {dogfish_material_set}")

		if len(command_list) == 6:
			scope = command_list[1]
			if command_list[0] == "loop":
				role = " ".join(command_list[4:6])
				if role in ["Primary Gray","Unlabeled Loopback"]:
					try:
						ip = IPNetwork(command_list[2])
						if ip.prefixlen == 32 and ip.version == 4:
							#
							allocated = dfish.dogfish_provision_prefix_loop(scope,command_list[2],command_list[3],role)
							if allocated:
								print("Allocated")
							else:
								print(bcolors.red,"Permission Error:",bcolors.end," please clone TT https://tt.amazon.com/0501648836 or ask neteng-is-deployment for permission to the parent prefix.")
						else:
							print("      Wrong IP format")
					except:
						print("      Wrong IP format")
				else:
					print("      Wrong Role.")

			elif command_list[0] == "p2p":
				role = command_list[5]
				if role in ["P2P","CSC","Internet"]:
					try:
						ip = IPNetwork(command_list[2])
						if ip.prefixlen == 31 and ip.version == 4:
							name = "{}<>{}".format(command_list[3],command_list[4])
							allocated = dfish.dogfish_provision_prefix_p2p(scope,command_list[2],name,role)
							if allocated:
								print("Allocated")
							else:
								print(bcolors.red,"Permission Error:",bcolors.end," please clone TT https://tt.amazon.com/0501648836 or ask neteng-is-deployment for permission to the parent prefix.")
						else:
							print("      Wrong IP format")
					except:
						print("      Wrong IP format.")
				else:
					print("      Wrong Role.")
			else:
				print("      Wrong request type.")

		elif len(command_list) == 4:
			scope = command_list[1]
			if command_list[0] == "sostenuto":
				role = "Sostenuto"
				try:
					ip = IPNetwork(command_list[2])
					if (ip.prefixlen == 31 or ip.prefixlen == 30) and ip.version == 4:
						allocated = dfish.dogfish_provision_prefix_sostenuto(scope,command_list[2],command_list[3],role)
						if allocated:
							print("Allocated")
						else:
							print(bcolors.red,"Permission Error:",bcolors.end," please clone TT https://tt.amazon.com/0501648836 or ask neteng-is-deployment for permission to the parent prefix.")
					else:
						print("      Wrong IP format")
				except:
					print("      Wrong IP format")

		elif len(command_list) == 3:
			scope = command_list[1]
			if command_list[0] == "delete":
				try:
					ip = IPNetwork(command_list[2])
					if (ip.prefixlen == 32 or ip.prefixlen == 31 or ip.prefixlen == 30) and ip.version == 4:
						deleted = dfish.dogfish_delete_prefix(scope,command_list[2])
						if deleted:
							print("Deleted")
						else:
							print(bcolors.red,"Permission Error:",bcolors.end," please clone TT https://tt.amazon.com/0501648836 or ask neteng-is-deployment for permission to the parent prefix.")
					else:
						print("      Wrong IP format")
				except:
					print("      Wrong IP format")


	def default(self,args):
		pass

	def emptyline(self):
		pass

	def do_help(self,args):
		print(bcolors.end)
		print("new <MCM>      New cutsheet for VC-COR deployment")
		print("show [site]    Shows deployments and their status")
		print("auto <site>    Automatically moves deployment to the next step")
		print(muda_progress_legend)
		print()

	def do_exit(self,args):
		print(bcolors.end)
		raise SystemExit

#******************************************#
def main():
	verbose = False
	if len(sys.argv) == 2:
		if sys.argv[1] in "--verbose":
			verbose = True

	global cutsheets,peers,loopbacks,vccors,vccars,brkcts,created_files
	global user,ncb,mcm_data,tiedown,bgp_communities,modeledcm,df,devicex,dogfish_material_set
	
	dogfish_material_set = "com.amazon.credentials.isengard.894712427633.user/dx-deploy-df-user"
	user = {}
	user["username"] = getpass.getuser()
	user["muda_path"] = os.path.expanduser("~")
	user["gb_path"] = os.path.expanduser("~")+"/GenevaBuilder"
	ncb = os.uname()[1]

	mcm_data = {}
	mcm_data["hostnames"] = ""
	mcm_data["create"] = ""
	mcm_data["diffs"] = ""
	mcm_data["deploy"] = ""
	mcm_data["steps"] = []

	muda_mkdir()
	modeledcm = mcm.mcm_api_connector()
	df = dogfish.DogFish(dogfish_material_set,verbose)
	cutsheets = []
	vccors = []
	vccars = []
	brkcts = []
	devicex = []
	peers = {}
	loopbacks = {}
	created_files = {}
	tiedown = {}
	bgp_communities = wiki.wiki_read_bgp_communities()

	muda_table = ddb.get_ddb_table('muda_table')
	muda_dict = ddb.scan_full_table(muda_table)

	possible_bricks = [x['brick'] for x in muda_dict]
	prompt = MyPrompt(possible_bricks)
	prompt.cmdloop()

#******************************************#
if __name__ == '__main__':
	main()

