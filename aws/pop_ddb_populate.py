#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import bisect
import collections
import concurrent.futures
import datetime
import decimal
import functools
import logging
import pathlib
import pprint
import random
import re
import signal
import time

import boto3
from dxd_tools_dev.datastore import ddb, s3
from dxd_tools_dev.modules import jukebox, netvane, nsm
from isd_tools_dev.modules import nsm as nsm_isd

# Enables quick termination of script if needed
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',


# logger = logging.getLogger()
# Logging is disabled because of NetVane logger that sprays console messages
# logging.basicConfig(
#     format="%(asctime)s - %(message)s",
#     datefmt="%d-%b-%y %H:%M:%S",
#     level=logging.CRITICAL,
#
# logger.disabled = True


# Logging enabled for DJS debugging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)


def vc_devices(region: str) -> list:
    """Search existing PoP for VC Devices - return found devices

    Args:
        pop (str): PoP to be searched
    """
    # region = jukebox.get_site_region_details(pop).region.realm
    nsm_car = nsm.get_devices_from_nsm("vc-car", regions=region)
    jb_car = jukebox.get_devices_in_jukebox_region(region,'in-service','car')

    nsm_cas = nsm.get_devices_from_nsm("vc-cas", regions=region)
    jb_cas = jukebox.get_devices_in_jukebox_region(region,'in-service','cas')

    all_car = nsm_car + jb_car
    all_cas = nsm_cas + jb_cas

    car_devs = sorted(set(all_car))
    cas_devs = sorted(set(all_cas))

    return car_devs + cas_devs

def customer_count(ports: dict) -> dict:
    """ Count customer-facing 10Gb/100Gb interfaces that are currently
    in use

    Args:
        ports (dict): interface information

    Returns:
        dict: aggregate count of 10Gb interfaces being used by customers
    """
    status = {k: 0 for k in ports}
    for x in status:
        onegb_ports = len(
            [
                xx
                for xx in ports[x]
                if "customer" in xx["Description"] and "ge-" in xx["Name"]
            ]
        )
        tengb_ports = (
            len(
                [
                    xx
                    for xx in ports[x]
                    if "customer" in xx["Description"] and "xe-" in xx["Name"]
                ]
            )
            * 10
        )
        hundgb_ports = (
            len(
                [
                    xx
                    for xx in ports[x]
                    if "customer" in xx["Description"] and "et-" in xx["Name"]
                ]
            )
            * 100
        )
        status[x] = onegb_ports + tengb_ports + hundgb_ports
    return status


def pop_tier(i: int) -> str:
    """ Determine tier of PoP

    Args:
        i (int): Aggregate customer-facing capacity

    Returns:
        str: returns PoP tier
    """
    if 300 >= i:
        return "Small"
    elif 300 < i <= 999:
        return "Medium"
    elif i > 999:
        return "Large"


def aggregate_band(info: dict) -> dict:
    """ Aggregate customer-facing capacity per PoP

    Args:
        info (dict): dict of devices with customer-facing capacity as value

    Returns:
        dict: returns agg customer-facing capacity per PoP 
    """
    agg = collections.defaultdict(int)
    for k, v in info.items():
        agg[k.split("-")[0]] += v
    return dict(agg)


def get_car_border_agg(sp: str, backhaul_check=False, device_check=False) -> dict:
    """Obtain border backhaul for Pioneer/DX-Small sites

    Args:
        sp (str): device 
        backhaul_check (bool, optional): Specify backhaul functionality to be run - Defaults to False.
        device_check (bool, optional): Specify device verification functionality to be run - Defaults to False.

    Returns:
        dict: return agg bandwidth per border device
    """
    border_check = ["vc-dar", "br-tra", "vc-cor"]
    car_agg = {}
    bord_agg = collections.defaultdict(int)
    container = collections.defaultdict(list)
    a_info = nsm_isd.get_raw_device(sp)
    get_neigh = [xx for xx in a_info["interfaces"] if "neighbors" in xx]
    for xx in get_neigh:
        if "physical" in xx["class"] and "up" in xx["admin_status"]:
            if xx["neighbors"]["link_layer"]["device_name"] is not None:
                if any(
                    yy in xx["neighbors"]["link_layer"]["device_name"].lower()
                    for yy in border_check
                ):
                    if backhaul_check:
                        container[sp].append(
                            (
                                xx["neighbors"]["link_layer"]["device_name"].lower(),
                                xx["bandwidth_mbit"],
                            )
                        )
    if container:
        if backhaul_check:
            for _, v in container.items():
                for vv in v:
                    bord_agg[vv[0]] += int(vv[1])
            car_agg[sp] = dict(bord_agg)
            return car_agg


def car_border_agg(pop: str, primary: str, devices: list) -> dict:
    """ Filter Active/Passive parent sites from agg backhaul metric

        Args:
            pop (str): PoP name
            primary (str): Active parent site
            devices (list): List of devices to verify

        Returns:
            dict: Agg capacity per active parent for Pioneer/DX-Small sites
    """
    pop_agg = collections.defaultdict(int)
    if not pop_agg:
        dx_info = [get_car_border_agg(x, backhaul_check=True) for x in devices]
        dar_check = {
            vv for x in dx_info for k, v in x.items() for vv in v if "vc-dar" in vv
        }
        if len(dar_check) >= 2:
            dx_info = [get_car_border_agg(x, backhaul_check=True) for x in dar_check]
        if dx_info:
            for i in range(0, len(dx_info)):
                for _, v in dx_info[i].items():
                    for tra, cap in v.items():
                        if ("br-tra" and primary in tra) or (
                            "vc-cor" and primary in tra
                        ):
                            pop_agg[pop] += cap // 1000
    return pop_agg


@functools.lru_cache(maxsize=128)
def pop_info(pop_info) -> dict:
    """ LRU Cache for DynamoDB table

    Args:
        pop_info ([type]): DynamoDB table name

    Returns:
        dict: cached DynamoDB dict
    """
    pop_table = ddb.scan_full_table(pop_info)
    return pop_table


def recomm_oversub(
    custer_facing: int, border_facing: int, oversub_rate: float, speed=None
) -> str:
    """ Calculate recommended backhaul bandwidth that would adjust the
    oversubscription ratio within a standard

    Args:
        custer_facing (int): customer-facing capacity
        border_facing (int): border-facing capacity
        oversub_rate (float): current oversubscription rate
        speed (int, optional): interface speed (needed for bandwidth increments)

    Returns:
        str: return recommended backhaul bandwidth and oversub ratio
    """
    cap = border_facing
    over = oversub_rate
    threshold = 4.5
    while threshold <= over:
        cap += speed
        over = custer_facing / cap
    return cap, "{}:1".format(round(over, 1))


@functools.lru_cache(maxsize=128)
def obtain_bgp_info() -> dict:
    """ Extract customer-facing BGP peerings from S3 bucket

    Returns:
        dict: nested dict containing devices and customer-facing BGP peering sessions
    """
    c = collections.defaultdict(dict)
    bgp_bucket = s3.DXToolsS3(s3_client=boto3.client).create()
    dl_files = bgp_bucket.list_files_in_bucket("dxbi-pop-assessment")
    if dl_files:
        bucket_files = "".join(dl_files)
        status = bgp_bucket.s3_bucket_file_download(bucket_files, "dxbi-pop-assessment")
        if not "ERROR" in status:
            filename, _, _, _, _, home_dir = status.split(" ")
            with open("{}/{}".format(home_dir, filename), "r") as f:
                output = [x.replace("\n", "") for x in f.readlines()]
            for info in output:
                # Specify IPv4 BGP peerings for now
                device, devtype, _, count = info.split("!")
                # Specify VC-CAR devices for now
                if "car" in devtype:
                    c[device.split("-")[0]][device] = count
    return dict(c)


def verify_bgp_thresh(
    x: dict, pop: str, breakpoints=[1000, 2000, 2700, 3000], grades="ABCDE"
):
    """ Obtain informational status regarding customer-facing BGP peerings at a PoP

    Args:
        x (dict): dict containing customer-facing BGP peerings
        pop (str): PoP locator
        breakpoints (list, optional): Threshold(s) for grading. Defaults to [1000, 2000, 2700, 3000].
        grades (str, optional): Key/value mapping for informational messaging. Defaults to "ABCDE".

    Returns:
        dict, str: returns dict of BGP-peerings per device and informational message
    """
    bgp_alarm = {
        "A": "No Concern",
        "B": "Normal",
        "C": "Concerning",
        "D": "Control-plane breach is possible",
        "E": "Control-plane breach is imminent",
    }
    status = "A"
    for _, v in sorted(x[pop].items(), key=lambda x: int(x[1])):
        i = bisect.bisect(breakpoints, int(v))
        status = grades[i]
    return x[pop], bgp_alarm[status]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def brd_util(devices: list, region: str) -> dict:
    """ Extract max weekly utilization from DX -> border devices based ifTrafficOut/ifTrafficIn
    metrics retrieved from NetVane
    Args:
        devices (list): list of DX devices in Region
    Returns:
        dict: aggregated max weekly DX -> border per PoP
    """
    status = None
    collect = collections.defaultdict(lambda: collections.defaultdict(dict))
    temp_agg = collections.defaultdict(dict)
    agg_collect = collections.defaultdict(int)
    # Initialize dict that will be returned
    reorg_agg = {k.split("-")[0]: 0 for k in devices}
    if "bjs" in region:
        status = "bjs"
        #return reorg_agg
    chnk = list(chunks(devices, 2))
    regex = "^ae[0-9]{1,2}[^\.]*(br-tra|vc-dar|vc-cor)"
    for x in chnk:
        wait = random.randrange(3)
        time.sleep(wait)
        test = netvane.get_interfaces_traffic_max_week(x, element_regex=regex, region=status)
        for x in test:
            if "ifTrafficOut" in x["Metric"]:
                collect[x["Device_Name"]][x["Interface"]][x["Metric"]] = round(
                    x["Value"] / 1000000000, 2
                )
            if "ifTrafficIn" in x["Metric"]:
                collect[x["Device_Name"]][x["Interface"]][x["Metric"]] = round(
                    x["Value"] / 1000000000, 2
                )
    for k, v in dict(collect).items():
        for x, y in v.items():
            temp_agg[k][x] = max(y["ifTrafficIn"], y["ifTrafficOut"])
    for k, v in temp_agg.items():
        for _, band in v.items():
            agg_collect[k.split("-")[0]] += band
    reorg_agg = {
        k: decimal.Decimal(str(round(v, 2))) for k, v in dict(agg_collect).items()
    }
    return reorg_agg

def obtain_brd_devices(pop: str, brd_info: dict, misc_devices: dict) -> dict:
    """ Extract border-device types that DX devices peer with
    for backhaul purposes

    Args:
        pop (str): PoP descriptor
        brd_info (dict): border peering information

    Returns:
        dict: return dict of border devices type(s) found
    """
    pop_devices = collections.defaultdict(list)
    border_devices = {
        "vc-cor": False,
        "br-tra": False,
        "vc-dar": False,
        "br-kct": False,
    }
    tc_pop_info = [t for t in brd_info if pop in t["Site"].lower()]
    for x in tc_pop_info:
        for p in x["Devices_Bandwidth_Gbps"]:
            for xx in p["interfaces"]:
                if "vc-cor" in xx["description"]:
                    border_devices["vc-cor"] = True
                if "vc-dar" in xx["description"]:
                    border_devices["vc-dar"] = True
                if "br-kct" in xx["description"]:
                    border_devices["br-kct"] = True
                if "br-tra" in xx["description"]:
                    border_devices["br-tra"] = True
    for k, v in border_devices.items():
        if v:
            pop_devices[pop].append(k.upper())
    if pop_devices:
        return pop_devices
    # Needed for Titan devices that don't have standard backhaul req
    return {pop: ["N/A"]}


def util_brdr_trend(pop: str, curr_band: int, region: str, dynamo_table) -> dict:
    """ Obtain trending metrics for backhaul utilization

    Args:
        pop (str): PoP locator
        curr_band (int): current utilization metric for PoP (aggregate)
        region (str): region locator
        dynamo_table ([type]): DynamoDB table

    Returns:
        dict: dict of tuples containing trending info
    """
    region_flag = True if "bjs" in region else False
    border_trending = {}
    extract_info = {}
    fail_info = {}
    bjs_info = {}
    if region_flag:
        # Flagging BJS region
        bjs_info[pop] = (0, curr_band, "NOCHANGE-BJSFLAGGED", 0, curr_band, curr_band)
        return bjs_info
    pop_dict = pop_info(dynamo_table)
    if pop_dict:
        # Need to extract region for dual-region PoP's
        region_extract = [x for x in pop_dict if region in x["Region"]]
        for l in region_extract:
            if pop == l["PoP"]:
                extract_info.update(l)
    else:
        fail_info[pop] = (0, 0, "NOCHANGE", "0.00%", curr_band, curr_band)
        return fail_info

    if extract_info:
        # TODO: Add weekly verification logic to save processing cycles

        #  PoP   weekly-delta    previous-wk         trend     %change    max    min
        # gru3 : (   28,             30,            'NOCHANGE',    5%,     50,     9 )

        if "AggDxBrdrBandwidthUtil" in extract_info:
            if "AggDxBrdrBandwidthMax" in extract_info:
                max_value = max(extract_info["AggDxBrdrBandwidthMax"], curr_band)
            else:
                max_value = max(extract_info["AggDxBrdrBandwidthUtil"], curr_band)
            if "AggDxBrdrBandwidthMin" in extract_info:
                min_value = min(extract_info["AggDxBrdrBandwidthMin"], curr_band)
            else:
                min_value = min(extract_info["AggDxBrdrBandwidthUtil"], curr_band)
            prev = extract_info["AggDxBrdrBandwidthUtil"]
            diff = 100 * (curr_band - prev) / prev
            if curr_band > prev:
                border_trending[pop] = (
                    curr_band - prev,
                    prev,
                    "INCREASING",
                    "{}%".format(round(diff, 2)),
                    max_value,
                    min_value,
                )
            elif curr_band < prev:
                border_trending[pop] = (
                    curr_band - prev,
                    prev,
                    "DECREASING",
                    "{}%".format(round(diff, 2)),
                    max_value,
                    min_value,
                )
            else:
                border_trending[pop] = (
                    curr_band - prev,
                    prev,
                    "NOCHANGE",
                    "{}%".format(round(diff, 2)),
                    max_value,
                    min_value,
                )
        else:
            border_trending[pop] = (
                0,
                0,
                "NOCHANGE",
                "0.00%",
                curr_band,
                curr_band,
            )

    return border_trending


@functools.lru_cache(maxsize=128)
def backhaul_band(info: tuple, devices: tuple) -> dict:
    """ Obtain backhaul/border facing information from DynamoDB
    table that riazqama@ created

    Args:
        info (tuple): list of PoP's (has to be tuple data structure due to LRU_cache functionality)

    Returns:
        dict: two dictionaries are returned containing capacity/device-type info
    """
    pioneer_sites = {
        "ams53": {"primaryPop": "ams54", "backupPop": "ams1", "flip": "False"},
        "iad53": {"primaryPop": "iad4", "backupPop": "iad2", "flip": "False"},
        "bom52": {"primaryPop": "bom50", "backupPop": "bom51", "flip": "False"},
        "lax51": {"primaryPop": "lax1", "backupPop": "lax3", "flip": "False"},
        "ord52": {"primaryPop": "ord51", "backupPop": "ord50", "flip": "False"},
        "dub65": {"primaryPop": "dub2", "backupPop": "dub3", "flip": "False"},
        "dub4": {"primaryPop": "dub3", "backupPop": "dub2", "flip": "False"},
        "dub7": {"primaryPop": "dub2", "backupPop": "dub3", "flip": "False"},
        "sfo20": {"primaryPop": "sfo4", "backupPop": "sfo5", "flip": "False"},
        "phx51": {"primaryPop": "phx50", "backupPop": "dfw3", "flip": "False"},
        "icn57": {"primaryPop": "icn54", "backupPop": "icn50", "flip": "False"},
        "cdg55": {"primaryPop": "cdg50", "backupPop": "cdg52", "flip": "False"},
    }
    dx_small_pops = {
        "sfo50": {"primaryPop": "sfo4", "backupPop": "sfo5"},
        "ewr53": {"primaryPop": "jfk1", "backupPop": "jfk6"},
        "iad53": {"primaryPop": "iad4", "backupPop": "iad2"},
        "dub65": {"primaryPop": "dub2", "backupPop": "dub3"},
        # "sfo20": {"primaryPop": "sfo5", "backupPop": "sfo4"},
        "gamma": {"primaryPop": "iad28", "backupPop": "iad21"},
    }
    dev_collection = collections.defaultdict(list)
    backhaul_devices = {}
    extract_haul_info = {}
    if devices:
        for x in devices:
            dev_collection[x.split("-")[0]].append(x)
    tc_info = ddb.get_ddb_table("tc_pop_border_capacity_table")
    tc_dict = ddb.scan_full_table(tc_info)
    obtain_devices = [obtain_brd_devices(x, tc_dict, dev_collection) for x in info]
    if obtain_devices:
        for o in obtain_devices:
            backhaul_devices.update(dict(o))
    tc_haul_info = {t["Site"].lower(): int(t["Site_Bandwidth_Gbps"]) for t in tc_dict}
    for p in info:
        # Extract only active Pioneer/Small-PoP sites for capacity verification
        if p in pioneer_sites or p in dx_small_pops:
            if p in pioneer_sites:
                pioneer_agg = car_border_agg(
                    p, pioneer_sites[p]["primaryPop"], dev_collection[p],
                )
                if pioneer_agg:
                    extract_haul_info.update(pioneer_agg)
            elif p in dx_small_pops:
                dx_small_agg = car_border_agg(
                    p, dx_small_pops[p]["primaryPop"], dev_collection[p],
                )
                if dx_small_agg:
                    extract_haul_info.update(dx_small_agg)
        elif p in tc_haul_info:
            extract_haul_info[p] = tc_haul_info[p]
        else:
            extract_haul_info[p] = 0
    return extract_haul_info, backhaul_devices


# TODO: Will be removed - https://issues.amazon.com/AWSDXUI-214 will supply this data in the near future
# def hist_customer_info(pop: str, band: int, region: str, dynamo_table) -> dict:
#     """ Experimental function to keep track of customer capacity on a weekly/monthly/yearly basis


#     Args:
#         pop (str): PoP locator
#         band (int): customer-facing capacity information
#         region (str): regoin locator
#         dynamo_table ([type]): DynamoDB table

#     Returns:
#         dict: dictionary of tuples containing weekly/monthly/yearly customer-facing capacity diff's
#     """
#     cust_diff = collections.defaultdict(tuple)
#     extract_info = {}
#     pop_dict = pop_info(dynamo_table)
#     if pop_dict:
#         # Need to extract region for dual-region PoP's
#         region_extract = [x for x in pop_dict if region in x["Region"]]
#         for l in region_extract:
#             if pop == l["PoP"]:
#                 extract_info.update(l)
#     else:
#         cust_diff[pop] = (0, 0, 0)

#     if extract_info:
#         prev = datetime.datetime.strptime(extract_info["Timestamp"], "%Y-%m-%d %H:%M")
#         now = datetime.datetime.now()
#         p_week, c_week = (
#             datetime.datetime.date(prev).isocalendar()[1],
#             datetime.datetime.date(now).isocalendar()[1],
#         )
#         p_month, c_month = prev.month, now.month
#         p_year, c_year = (
#             datetime.datetime.date(prev).isocalendar()[0],
#             datetime.datetime.date(now).isocalendar()[0],
#         )
#         try:
#             if p_year == c_year and "AggCustomerBandwidthDiffYr" in extract_info:
#                 logging.info("Years are a match")
#                 logging.info(
#                     f"band: {band} extract_info: {int(extract_info['AggCustomerBandwidth'])} yr_diff: {int(extract_info['AggCustomerBandwidthDiffYr'])}"
#                 )
#                 yr = (band - int(extract_info["AggCustomerBandwidth"])) + int(
#                     extract_info["AggCustomerBandwidthDiffYr"]
#                 )
#                 if (
#                     p_month == c_month
#                     and "AggCustomerBandwidthDiffMnth" in extract_info
#                 ):
#                     logging.info("Months are a match")
#                     logging.info(
#                         f"band: {band} extract_info: {int(extract_info['AggCustomerBandwidth'])} yr_diff: {int(extract_info['AggCustomerBandwidthDiffMnth'])}"
#                     )
#                     mnth = (band - int(extract_info["AggCustomerBandwidth"])) + int(
#                         extract_info["AggCustomerBandwidthDiffMnth"]
#                     )
#                     if (
#                         p_week == c_week
#                         and "AggCustomerBandwidthDiffWk" in extract_info
#                     ):
#                         logging.info("Weeks match")
#                         logging.info(
#                             f"band: {band} extract_info: {int(extract_info['AggCustomerBandwidth'])} yr_diff: {int(extract_info['AggCustomerBandwidthDiffWk'])}"
#                         )
#                         wk = (band - int(extract_info["AggCustomerBandwidth"])) + int(
#                             extract_info["AggCustomerBandwidthDiffWk"]
#                         )
#                     else:
#                         logging.info("Weeks DO NOT match")
#                         wk = 0
#                 else:
#                     logging.info("Months DO NOT match")
#                     mnth = 0
#             else:
#                 logging.info("Years DO NOT match")
#                 yr = mnth = wk = 0
#             cust_diff[pop] = (yr, mnth, wk)
#         except:
#             pass

#     return dict(cust_diff)


def dynamo_create(
    region: str,
    d: dict,
    brd_info: dict,
    brd_devices: dict,
    p: dict,
    scale_table,
    brdf_devices: list,
) -> dict:
    """ Create table to uploaded to DynamoDB

        Args:
            region (str): region of specified devices
            d (dict): customer-facing capacity information
            p (dict): customer-facing PoP information

        Returns:
            dict: returns dict of DynamoDB upload info
        """
    customer_bgp_info = obtain_bgp_info()
    # burn_rate_agg = {}
    brdr_trend_info = {}
    bkhaul_util = brd_util(brdf_devices, region)
    brdr_trend = [
        util_brdr_trend(k, v, region, scale_table) for k, v in bkhaul_util.items()
    ]
    for t in brdr_trend:
        brdr_trend_info.update(t)
    dyndb = collections.defaultdict(dict)
    cust_pop = collections.defaultdict(dict)
    # burn_rate_verify = [
    #     hist_customer_info(x, y, region, scale_table) for x, y in d.items()
    # ]
    # for b in burn_rate_verify:
    #     burn_rate_agg.update(b)
    for k, v in p.items():
        cust_pop[k.split("-")[0]][k] = "{}Gb".format(v)
    try:
        for x, y in d.items():
            bgp_sessions, bgp_status = verify_bgp_thresh(customer_bgp_info, x)
            logging.info(f"Adding {x} to dict for DDB Table")
            dyndb[x]["PoP"] = x
            dyndb[x]["Type"] = pop_tier(y)
            dyndb[x]["Region"] = region
            dyndb[x]["Timestamp"] = time.strftime("%Y-%m-%d %H:%M")
            dyndb[x]["AggDxBrdrBandwidthUtil"] = (
                bkhaul_util[x] if x in bkhaul_util else 0
            )
            if dyndb[x]["Type"] == 'Large' and dyndb[x]["AggDxBrdrBandwidthUtil"] < 320:
                dyndb[x]["Type"] = 'Medium'

            if dyndb[x]["Type"] == 'Medium' and dyndb[x]["AggDxBrdrBandwidthUtil"] < 160:
                dyndb[x]["Type"] = 'Small'

            dyndb[x]["AggCustomerBandwidth"] = y
            # dyndb[x]["AggCustomerBandwidthDiffWk"] = (
            #     burn_rate_agg[x][2] if x in burn_rate_agg else 0
            # )
            # dyndb[x]["AggCustomerBandwidthDiffMnth"] = (
            #     burn_rate_agg[x][1] if x in burn_rate_agg else 0
            # )
            # dyndb[x]["AggCustomerBandwidthDiffYr"] = (
            #     burn_rate_agg[x][0] if x in burn_rate_agg else 0
            # )
            dyndb[x]["AggBackHaulBandwidth"] = brd_info[x]
            dyndb[x]["CustomerFacingPortUtil"] = cust_pop[x]
            dyndb[x]["BorderFacingDevices"] = brd_devices[x]
            dyndb[x]["CustBGPSessionInfo"] = bgp_sessions
            dyndb[x]["CustBGPSessionStatus"] = bgp_status
            if brd_info[x] > 0:
                dyndb[x]["PotentialOverSubscripRatio"] = "{}:1".format(
                    str(round(y / brd_info[x], 1))
                )
            if x in bkhaul_util:
                if bkhaul_util[x] == 0:
                    dyndb[x]["AggDxBrdrBandwidthPrcnt"] = "0%"
                else:
                    dyndb[x]["AggDxBrdrBandwidthPrcnt"] = "{}%".format(
                        round((100 * int(bkhaul_util[x])) / int(brd_info[x]))
                    )
                actual_oversub = str(round(bkhaul_util[x] / brd_info[x], 2))
                dyndb[x]["ActualOverSubscripRatio"] = "{}:1".format(actual_oversub)
                dyndb[x]["AggDxBrdrBandwidthMin"] = brdr_trend_info[x][5]
                dyndb[x]["AggDxBrdrBandwidthMax"] = brdr_trend_info[x][4]
                dyndb[x]["AggDxBrdrBandwidthUtilTrend"] = brdr_trend_info[x][2]
                dyndb[x]["AggDxBrdrBandwidthUtilPercentDiff"] = brdr_trend_info[x][3]
                dyndb[x]["AggDxBrdrBandwidthUtilWklyDiff"] = brdr_trend_info[x][0]

            logging.info(f"PoP {x} has been added to dict for DDB Table")
    except Exception as e:
        logging.info(x, e)

    return dyndb


def vc_info(locator: str, x: list, table):
    # interim_scale_table = ddb.get_ddb_table("pop_info")
    scale_table = ddb.get_ddb_table("pop_size")
    legacy_devices = {l for l in x if not re.findall(r"-v[1234]-", l)}
    phx_devices = {l for l in x if ("vc-car" not in l and re.findall(r"-v[1234]-", l))}
    phx_brd_devices = {l for l in x if ("vc-car" in l and re.findall(r"-v[1234]-", l))}
    customer_facing, border_facing = (
        list(legacy_devices) + list(phx_devices),
        list(legacy_devices) + list(phx_brd_devices),
    )
    if len(customer_facing) >= 1:
        car_hdware = {}
        for c in customer_facing:
            try:
                car_hdware[c] = ddb.get_device_from_table(table, "Name", c)["Hardware"]
            except:
                pass
        if car_hdware:
            ports = {
                k: ddb.get_device_from_table(table, "Name", k)["Interfaces"]
                for k in car_hdware
            }
            # ports = {k: nsm.get_device_interfaces_from_nsm(k) for k in car_hdware}
            output = customer_count(ports)
            agg_info = aggregate_band(output)
            border_info, border_devices = backhaul_band(
                tuple(agg_info), tuple(border_facing)
            )
            upload = dynamo_create(
                locator,
                agg_info,
                border_info,
                border_devices,
                output,
                scale_table,
                border_facing,
            )
            pprint.pprint(dict(upload))
            print()
            for _, xx in dict(upload).items():
                logging.info(f"PoP {xx} is being added to DDB Table")
                ddb.put_item_to_table(scale_table, xx)


def concurr_f(func, xx: dict, *args, **kwargs) -> list:
    f_result = []
    # Limiting max_workers to 4 otherwise DyanmoDB API will initiate rate-limiting
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(func, x, y, *args, **kwargs): x for x, y in xx.items()
        }
        for future in concurrent.futures.as_completed(futures):
            _ = futures[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                pass
    return f_result if f_result else None


def main():
    table = ddb.get_ddb_table("dx_devices_table")
    regions = [
        "arn",
        "bah",
        "bjs",
        "bom",
        "cdg",
        "cmh",
        "cpt",
        "dub",
        "fra",
        "gru",
        "hkg",
        "iad",
        "icn",
        "kix",
        "lhr",
        "mxp",
        "nrt",
        "pdx",
        "sfo",
        "sin",
        "syd",
        "yul",
        "zhy",
    ]
    vc_agg_info = {k: vc_devices(k) for k in regions}
    _ = concurr_f(vc_info, vc_agg_info, table)
    # pop_info = [vc_info(k, v, table) for k, v in vc_agg_info.items()]


if __name__ == "__main__":
    main()

