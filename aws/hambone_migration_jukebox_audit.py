#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import argparse
import sys
from dxd_tools_dev.modules import dogfish, wiki, dns, mcm, cr, nsm, mwinit_cookie, jukebox, region_local, hercules, simissue
import subprocess
import re
import collections
from time import perf_counter

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

site = input ("Please provide site name to perform Audit on Edg and CIR devices eg. sfo9: " )
sim = input("Do you want to create sim for tracking purpose?")
def get_all_edg_cir_devices_site(site):
    commercial_edg_groups_list = list()
    site_details = jukebox.get_site_region_details(site)
    region = site_details.region.realm
    all_devices_site = jukebox.get_site_devices(site=site, state='in-service')
    cir_edg_all_list = list()

    for grp in site_details.region.edg_groups:
        if 'ExternalCustomer' == grp.edg_group_type:
            commercial_edg_groups_list.append(grp.name)
    for dev in all_devices_site:
        if 'vc-edg-r' in dev:
            edg_grp = jukebox.get_device_detail(dev).data.device.edg_group
            if edg_grp in commercial_edg_groups_list:
                cir_edg_all_list.append(dev)
        elif 'vc-cir' in dev:
            cir_edg_all_list.append(dev)

    return cir_edg_all_list

def get_peers_from_hercules_config(device):
    pattern = 'set protocols bgp .*vc-(bar|fab).*'
    hs_bar_peers = list()
    hs_fab_peers = list()
    try:
        matching_config = hercules.get_config_matching_pattern(device,pattern,stream='collected', file_list=['set-config'])
        if matching_config:
            for item in matching_config:
                if 'vc-fab' in item:
                    hs_fab_peers.append(item.split(' ')[-1])
                elif 'vc-bar' in item:
                    hs_bar_peers.append(item.split(' ')[-1])
        if hs_fab_peers and not hs_bar_peers:
            print (bcolors.OKGREEN,f'[Info] >>As per {device} config in Hercules, it is not migrated to HamboneV2.',bcolors.ENDC)
        elif not hs_fab_peers and hs_bar_peers:
            print (bcolors.OKGREEN,f'[Info] >>As per {device} config in Hercules, it is migrated to HamboneV2.',bcolors.ENDC)
        elif hs_fab_peers and hs_bar_peers:
            print (bcolors.FAIL,f'[ERROR] >>As per {device} config in Hercules, it is migrated to HamboneV2 but Fab config is still present, please take appropriate action to cleanup this config.',bcolors.ENDC)
        else:
            print(bcolors.OKGREEN,f'[INFO]No bar or fab peers present on {device}.',bcolors.ENDC)
 
    except Exception as error:
        sys.exit()
    
    return hs_bar_peers,hs_fab_peers

def get_peers_from_jukebox(device):
    jb_all_peers = list()
    unique_JB_bar_peers = list()
    unique_JB_fab_peers = list()
    try:
        jb_cabling_peers,jb_link_peers = jukebox.get_device_peers(device)
        jb_all_peers = list(jb_cabling_peers + jb_link_peers)
        for x in jb_all_peers:
            if 'vc-bar' in x and x not in unique_JB_bar_peers:
                unique_JB_bar_peers.append(x)
            elif 'vc-fab' in x and x not in unique_JB_fab_peers:
                unique_JB_fab_peers.append(x)
            else:
                pass
        if unique_JB_bar_peers:
            print (bcolors.OKBLUE,f'[Info] >>BAR Peers found in Jukebox.', unique_JB_bar_peers,bcolors.ENDC)
        else:
            print (bcolors.OKBLUE,f'[Info] >>No Bar Peers found in Jukebox.',bcolors.ENDC)
        if unique_JB_fab_peers:
            print (bcolors.OKGREEN,f'[Info] >>FAB Peers found in Jukebox.', unique_JB_fab_peers,bcolors.ENDC)
        else:
            print (bcolors.OKGREEN,f'[Info] >>No Fab Peers found in Jukebox.',bcolors.ENDC)
            
    except Exception as error:
        sys.exit()
        
    return unique_JB_bar_peers,unique_JB_fab_peers,jb_cabling_peers,jb_link_peers

def main():
    cab_link_cleanup = 'false'
    link_cleanup = 'false'
    cab_cleanup = 'false'
    no_cleanup = 'false'
    start_time = perf_counter()
    print (bcolors.HEADER,f'This Script will audit All Commercial EDG and CIR devices peers-status in Jukebox against Hercules for {site}. \n It can take 10-15 minutes to execute this script depending on number of edg groups in the site.\n',bcolors.ENDC)
    print (bcolors.HEADER,f' ** Starting Audit for all CIR and EDG devices in {site}: ',bcolors.ENDC)
    all_cir_edg_devices = get_all_edg_cir_devices_site(site)
    fix_devices = list()
    for device in all_cir_edg_devices:
        print (bcolors.HEADER,f'-----------------------------------------------',bcolors.ENDC)
        print (bcolors.BOLD,f'Starting Audit >> {device}:\n',bcolors.ENDC)
        hercules_bar_peers,hercules_fab_peers = get_peers_from_hercules_config(device)
        try:
            JB_bar_peers,JB_fab_peers,jb_cab_peers,jb_lk_peers = get_peers_from_jukebox(device)
        except Exception as error:
            sys.exit()

        if JB_bar_peers:
            if collections.Counter(JB_bar_peers) == collections.Counter(hercules_bar_peers):
                print(bcolors.CLEARBLUE,f'[Success] >> Hercules and Jukebox are in Sync for BAR peers for {device}',bcolors.ENDC)
            else:
                missing_peers = list(set(JB_bar_peers)-set(hercules_bar_peers))
                if missing_peers:
                    print(bcolors.CLEARBLUE,f'[Info] >> Hercules and Jukebox are not in Sync for {device}.\n Following Peers are not present on {device} but present in Jukebox: {missing_peers} \n This is acceptable as it shows migration is in progress.',bcolors.ENDC)
        if JB_fab_peers:
            if collections.Counter(JB_fab_peers) == collections.Counter(hercules_fab_peers):
                print(bcolors.CLEARBLUE,f'[Success] >> Hercules and Jukebox are in Sync for FAB peers for {device}',bcolors.ENDC)
            else:
                device_cleanup = {}
                missing_peers = list(set(JB_fab_peers)-set(hercules_fab_peers))
                if missing_peers:
                    if ((set (missing_peers) <= set (jb_lk_peers)) and (set (missing_peers) <= set (jb_cab_peers))):
                         cab_link_cleanup = 'true'
                         device_cleanup[device] = {'Peers to be cleaned': missing_peers, 'Clean Peers from Cabling and Link_CIDRs':cab_link_cleanup}
                         print(bcolors.FAIL,f'[Error] >> Please clean following peers {missing_peers} from Jukebox Cabling and Link CIDRs sections',bcolors.ENDC)
                    elif (set (missing_peers) <= set (jb_lk_peers)):
                         link_cleanup = 'true'
                         device_cleanup[device] = {'Peers to be cleaned': missing_peers, 'Clean Peers from Link_CIDRs':link_cleanup}
                         print(bcolors.FAIL,f'[Error] >> Please clean following peers {missing_peers} from Jukebox Link CIDRs section',bcolors.ENDC)
                    elif (set (missing_peers) <= set (jb_cab_peers)):
                         cab_cleanup = 'true'
                         device_cleanup[device] = {'Peers to be cleaned': missing_peers, 'Clean Peers from Cabling':cab_cleanup}
                         print(bcolors.FAIL,f'[Error] >> Please clean following peers {missing_peers} from Jukebox Link Cabling section',bcolors.ENDC)
                    else:
                         no_cleanup = 'true'
                         pass
                fix_devices.append(device_cleanup)
        print (bcolors.BOLD,f'\n Audit Complete >> {device}.\n',bcolors.ENDC)
        print (bcolors.HEADER,f'-----------------------------------------------',bcolors.ENDC)
    if fix_devices:
        fix_device_str = ' \n '.join([str(elem) for elem in fix_devices])
        if sim == 'N':
            print (bcolors.HEADER,f'SIM can be created',bcolors.ENDC)
        elif sim == 'Y':
            issue = simissue.SimIssue(odin_set='com.amazon.credentials.isengard.749865518066.user/dxdeploymenttools_SIM_update')
            title = "[" + site.upper() + "]" + " Jukebox Cleanup needed for following EDG and CIR devices in " + site.upper() + " post HamboneV2 migration."
            description = "Please perform jukebox cleanup for following devices in " + site + ":\n" + fix_device_str 
            sim_id = issue.create(title, description)
            print (bcolors.WARNING,f'[WARNING] >> Created a SIM to track the Jukebox Cleanup under work https://issues.amazon.com/{sim_id}',bcolors.ENDC)
    print (bcolors.HEADER,f' \n Audit complete >> {site}. \n',bcolors.ENDC)
    stop_time = perf_counter()
    runtime = stop_time - start_time
    print(bcolors.CLEARBLUE,f'[Info] : Script took {round(runtime)} seconds to execute the task',bcolors.ENDC)
if __name__ == "__main__":
    main()
