#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import mcm
from isd_tools_dev.modules import nsm
import argparse
import sys
import logging
import time
import os
import re

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description = "Create manual PCN MCMs")

parser.add_argument('-r', '--region', type = str, required = True, help = "in which region(s) you would like to run the manual PCN")
parser.add_argument('-t', '--deadline', type = str, required = False, default = "", help = "when the PCN campaign will expire, e.g. '2020-12-30 23:59'")
parser.add_argument('-d', '--device-type', type = str, required = False, default = "rrr", help = "device type, e.g. rrr, cir, edg")
parser.add_argument('-m', '--mcm_id', type = str, required = False, default = "", help = "Manual PCN MCM ID")

args = parser.parse_args()

class campaign_options(object):
    rrr_creation_options = "create --template vc-rr-pcn-rebase-nonhs --joshua-policy-args VARIANCE=10 --nsm-queries '"
    get_campaign_details = "get -xd -c "

def device_regex(device_type):
    devices_type_list = ['rrr']
    if len(device_type) != 3 or device_type not in devices_type_list:
        sys.exit()
    return f"#name:/.*-vc-{device_type}-r.*/"

def expiration_time(args):
    if not args.deadline:
        timestamp = time.time()
        end_timestamp = (timestamp // 86400 + 31) * 86400 - 60
        end_time_struct = time.localtime(end_timestamp)
        end_time = time.strftime("%Y-%m-%d %H:%M", end_time_struct)
    else:
        end_time = args.deadline
    return end_time

def campaign_cmd(args,operations):
    campaign_service_path = "/apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign "
    query_regex = args.region.upper() + device_regex(args.device_type)
    campaign_cmds = {
    'rrr': campaign_service_path + campaign_options.rrr_creation_options + query_regex + "' --deadline '" + expiration_time(args) + "' --metadata 'mcm=" + args.mcm_id + "'",
    'get_campaign_details': campaign_service_path + campaign_options.get_campaign_details + args.campaign_id
    }
    if operations == "create":
        return campaign_cmds.get(args.device_type)
    elif operations == "get":
        return campaign_cmds.get("get_campaign_details")

def campaign_details(args):
    device_id_pair = dict()
    get_cmd = campaign_cmd(args,"get")
    cmpgn_get_output = os.popen(get_cmd)
    cmpgn_get_output = cmpgn_get_output.read()
    device_pattern = re.compile(r'[\w]*-vc-[\w-]*\d*')
    bundle_id_pattern = re.compile(r'https://hercules.amazon.com/bundle-v2/[\w-]*')
    device_list = device_pattern.findall(cmpgn_get_output)
    bundle_id_list = bundle_id_pattern.findall(cmpgn_get_output)
    for i in range(len(device_list)):
        device_id_pair[device_list[i]] = bundle_id_list[i].split('/')[-1].strip()
    return device_id_pair

def get_physical_data_center_ids(args):
    site_list = []
    devices = nsm.search_devices_in_region(args.region, device_regex(args.device_type)[1:])
    for device_dict in devices['devices']:
        device = device_dict['name']
        site = device.split('-')[0]
        if site not in site_list:
            site_list.append(site)
    sites = ','.join(site_list)
    return sites


def dryrun_bundles(args):
    dryrun_list = ""
    hosts = ""
    dryrun_links = ""
    devices_bundle_dict = args.device_id_pair
    for device in devices_bundle_dict:
        hosts += device + "\n"
        dryrun_cmd = "/apollo/env/AlfredCLI-2.0/bin/alfred deploy --dry-run -b " + devices_bundle_dict[device]
        log.info(
            f"starting bundle dryrun on {device}"
        )
        if args.region.lower() in ['bjs', 'zhy']:
            dryrun_output = os.popen('ssh atlantis-rt-61001.bjs11.amazon.com "' + dryrun_cmd + '"')
        else:    
            dryrun_output = os.popen(dryrun_cmd)
        dryrun_output = dryrun_output.read()
        dryrun_link_pattern = re.compile("https://sphere.amazon.com/alfred/#/[\w/-]*")
        dryrun_link = dryrun_link_pattern.findall(dryrun_output)
        dryrun_links += f'[{device}]({dryrun_link[-1]})\n'

    print(dryrun_links)
    return hosts, dryrun_links

def create_mcm_steps(args):
    step_ixops = {'title':f'Inform IXOPS Oncall before starting MCM (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    step_netsupport = {'title':f'Check #netsupport slack channel for any Sev2s in the region/AZ (Activity)','time':2,'description':'Post in #dx-ops-escalation channel that work is commencing for the MCM'}
    submit_campaign = {'title': 'Submit Campaign', 'time':2,'description': f"```\nssh network-config-builder-12001.dub2.corp.amazon.com\n/apollo/env/NetworkDeviceCampaignServiceCLI/bin/campaign-service campaign submit -c {args.campaign_id}\n```"}
    mcm_steps = [step_ixops, step_netsupport, submit_campaign]

    return mcm_steps

def countdown(time_in_seconds : int, reason: str):

    print(f'''

Wait {str(time_in_seconds)} seconds before {reason} completes.

''')

    for seconds in range(time_in_seconds,-1,-1):
        countdown_message = "Resume in " + str(seconds) + " seconds"
        print(countdown_message,end = "")
        print("\b" * (len(countdown_message)),end = "",flush=True)

        time.sleep(1)

    log.info(
        "Script resumed!\n"
        )


if __name__ == "__main__":
    args.campaign_cmd = ""
    args.hosts = ""
    args.dryrun = ""
    args.campaign_id = ""

    try:
        args.sites = get_physical_data_center_ids(args)

        args.mcm_id,args.mcm_uuid,mcm_overview = mcm.mcm_creation("manual_pcn_rrr", args)

        log.info(
            f"Created MCM: https://mcm.amazon.com/cms/{args.mcm_id}"
            )

        args.campaign_cmd = campaign_cmd(args,"create")
        log.info(
            f"creating the manual campaign for {args.device_type} in {args.region.upper()}"
            )
        cmpgn_create_output = os.popen(campaign_cmd(args,"create"))
        cmpgn_create_output = cmpgn_create_output.read()
        cmpgn_id_pattern = re.compile('Created campaign ([\w-]*)')
        results = cmpgn_id_pattern.search(cmpgn_create_output)
        args.campaign_id = results.group(1)

        log.info(
            f"Campaign Link: https://hercules.amazon.com/campaign/{args.campaign_id}"
            )

        countdown(90, "campaign creation")
        args.device_id_pair = campaign_details(args)
        args.hosts, args.dryrun = dryrun_bundles(args)

        log.info(
            f"Updating campaign and bundle dryrun information in {args.mcm_id}"
            )

        title, mcm_overview = mcm.mcm_rrr_manual_pcn(args)

        mcm.mcm_update(args.mcm_id,args.mcm_uuid,mcm_overview,create_mcm_steps(args))

        print(f'''
Created Manual PCN MCM for {args.region.upper()}:
===============================
https://mcm.amazon.com/cms/{args.mcm_id}

Manual PCN Campaign:
===============================
https://hercules.amazon.com/campaign/{args.campaign_id}

Bundle Dryruns:
===============================
{args.dryrun}
        ''')

    except SystemExit:
        print("invalid/unsupported device type, please check your input.")

    except Exception:
        print("Script encountered an error, quiting...")
        sys.exit()
