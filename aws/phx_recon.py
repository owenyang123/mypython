#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
""" Brief python script verifies if border devices can accommodate capacity demand(s) for new deployment.
Example of usage is below:

/apollo/env/DXDeploymentTools/bin/phx_recon.py -l "bos50" #Audit BOS50 PoP for border capacity to accommodate new deployment
/apollo/env/DXDeploymentTools/bin/phx_recon.py -l "bos50" -m #Audit BOS50 PoP for border capacity to accommodate new deployment and show Netvane bandwidth utilization for VC devices
/apollo/env/DXDeploymentTools/bin/phx_recon.py -l "sfo50" #Audit SFO50 PoP for border capacity to accommodate new deployment searching (will crawl VC-DAR's for border neigbors)
"""


import argparse
import collections
import concurrent.futures
import datetime
import functools
import itertools
import logging
import platform
import re
import signal
import sys
import textwrap
import time
import warnings

from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.modules import (
    border_port_alloc,
    jukebox,
    netvane,
    nsm,
    vc_port_alloc,
)
from dxd_tools_dev.portdata import border as portdata
from isd_tools_dev.modules import nsm as nsm_isd

# Ignore warnings from modules
warnings.filterwarnings("ignore")

# Enables quick termination of script if needed
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',


logger = logging.getLogger()
# Logging is disabled because of NetVane logger that sprays console messages
# logging.basicConfig(
#     format="%(asctime)s - %(message)s",
#     datefmt="%d-%b-%y %H:%M:%S",
#     level=logging.CRITICAL,
#
logger.disabled = True

VERSION = "1.32"

AVAIL_PORT_DICT = {}
BR_DEVICES = set()
FAILED_DEVICES = {}
HARDWARE_INFO = {}
MISC_INFO = collections.defaultdict(set)
RESERVE_PORTS = True
VC_CAS_CHECK = {}
VC_COR_BRICK = False
VC_DAR_FOUND = False
VC_DEV_HWARE = {}


# Adding DynamoDB table as global VAR
TABLE = ddb.get_ddb_table("dx_devices_table")

PIONEER_SITES = {
    "ams53": ["ams54", "ams50"],
    "bom52": ["bom50", "bom51"],
    "cdg55": ["cdg50", "cdg52"],
    "dub4": ["dub2", "dub3"],
    "dub65": ["dub2", "dub3"],
    "dub7": ["dub2", "dub3"],
    "iad53": ["iad2", "iad4"],
    "icn57": ["icn50", "icn54"],
    "lax51": ["lax50", "lax3"],
    "ord52": ["ord50", "ord51"],
    "phx51": ["phx50", "dfw3"],
    "sfo20": ["sfo5", "sfo4"],
}


class CustomError(Exception):
    """Error in function"""

    def __init__(self, message, cause=None):
        """Initializer for Custom Function error handler

        :param str message: Error message
        :param cause: Exception that caused this error (optional)
        """
        super(CustomError, self).__init__(message)
        self.cause = cause


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


# Platform check
if not "network-config-builder" in platform.node():
    print(
        bcolors.FAIL
        + "[!][!] Script needs to be run from a network-config-builder host. Exiting"
        + bcolors.ENDC
    )
    sys.exit()


def parse_args() -> str:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
    Brief python script verifies if border devices can accommodate capacity demand(s) for new deployment builds
    """
        ),
    )
    p.add_argument(
        "-l",
        "--locator",
        help="PoP/AZ designator (ex: lax3)",
        type=str,
        default="lax3",
    )
    p.add_argument(
        "-bdt",
        "--border_device_type",
        help="type of border devices (ex: br-agg, br-tra)",
        type=str,
        default="br-tra,br-kct",
    )
    p.add_argument(
        "-vdt",
        "--vc_device_type",
        help="type of vc devices (ex: vc-car, vc-edg)",
        type=str,
        default="vc-car",
    )
    p.add_argument(
        "-m",
        "--max-bandwidth",
        help="Display max weekly bandwidth",
        action="store_true",
    )
    p.add_argument(
        "-d",
        "--disable_reserved",
        help="Disable checks for DX-Reserved ports on border devices (if applicable)",
        action="store_true",
    )
    return p.parse_args()


def args_check(x: str, manual=False, d=None, dx_check=True):
    print()
    print(bcolors.WARNING + "Verification checklist:" + bcolors.ENDC)
    if manual:
        if any(l.isdigit() for l in x):
            print(
                f"{bcolors.BOLD}AZ/PoP Verification:{bcolors.ENDC} {bcolors.OKGREEN}{x}{bcolors.ENDC}"
            )
            print(
                f"{bcolors.BOLD}Multi-Region Verification:{bcolors.ENDC} {bcolors.OKGREEN}{d}{bcolors.ENDC}"
            )
    else:
        if any(l.isdigit() for l in x):
            print(
                f"{bcolors.BOLD}AZ/PoP Verification:{bcolors.ENDC} {bcolors.OKGREEN}{x} ({airport_locator([x[0:3]])}){bcolors.ENDC}"
            )
            if x:
                print(
                    f"{bcolors.BOLD}Region Verification:{bcolors.ENDC} {bcolors.OKGREEN}{get_region(tuple(x))}{bcolors.ENDC}"
                )
        else:
            if x:
                print(
                    f"{bcolors.BOLD}Region Verification:{bcolors.ENDC} {bcolors.OKGREEN}{x}{bcolors.ENDC}"
                )
    if dx_check:
        print(
            f"{bcolors.BOLD}DX-Reserved Port Verification on Border Devices:{bcolors.ENDC} {bcolors.OKGREEN}Enabled{bcolors.ENDC}"
        )
    else:
        print(
            f"{bcolors.BOLD}DX-Reserved Port Verification on Border Devices:{bcolors.ENDC} {bcolors.FAIL}Disabled{bcolors.ENDC}"
        )
    print()


def intro_message():
    print()
    print(
        bcolors.HEADER
        + "##################################################################################################"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###### Program will verify if TRA's/KCT's can accommodate PHX deployment capacity demands  #######"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "##################################################################################################"
        + bcolors.ENDC
    )
    print()
    print(
        bcolors.BOLD
        + "Time script started: {}".format(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        + bcolors.ENDC
    )
    print(f"Script Version: {bcolors.OKGREEN}{VERSION}{bcolors.ENDC}")
    time.sleep(0.5)
    print()


def rundown(args: str):
    print(
        bcolors.HEADER
        + "Program will verify if TRA's/KCT's can accommodate PHX deployment capacity demands"
        + bcolors.ENDC
    )
    print()
    time.sleep(0.5)


def airport_locator(s: str) -> str:
    pop = "".join(s)
    pop_dict = {
        "AMS": "Amsterdam, NL",
        "ARN": "Stockholm, SE",
        "ATL": "Atlanta, US",
        "BAH": "Manama, BH",
        "BCN": "Barcelona, ES",
        "BJS": "Beijing, CN",
        "BLR": "Bangalore, IN",
        "BOM": "Mumbai, IN",
        "BOS": "Boston, US",
        "CBR": "Canberra, AU",
        "CDG": "Paris, FR",
        "CMH": "Columbus, US",
        "CPH": "Copenhagen, DK",
        "CPT": "Cape Town, ZA",
        "DEL": "New Delhi, IN",
        "DEN": "Denver, US",
        "DFW": "Dallas-Fort Worth, US",
        "DUB": "Dublin, IE",
        "DUS": "Dusseldorf, DE",
        "DXB": "Dubai, AE",
        "EWR": "Newark, US",
        "FJR": "Fujairah, UAE",
        "FRA": "Frankfurt am Main, DE",
        "GIG": "Rio De Janeiro, BR",
        "GRU": "Sao Paulo, BR",
        "HEL": "Helsinki, FI",
        "HIO": "Portland, US",
        "HKG": "Hong Kong, HK",
        "HYD": "Hyderabad, IN",
        "IAD": "Dulles, US",
        "IAH": "Houston, US",
        "ICN": "Seoul, KR",
        "JFK": "New York, US",
        "JNB": "Johannesburg, ZA",
        "KUL": "Kuala Lumpur, MY",
        "LAS": "Las Vegas, US",
        "LAX": "Los Angeles, US",
        "LHR": "London, GB",
        "MAA": "Chennai, IN",
        "MAD": "Madrid, ES",
        "MAN": "Manchester, GB",
        "MCI": "Kansas City, US",
        "MEL": "Melbourne, AU",
        "MIA": "Miami, US",
        "MRS": "Marseille, FR",
        "MSP": "Minneapolis, US",
        "MUC": "Munich, DE",
        "MXP": "Milan, IT",
        "NRT": "Tokyo, JP",
        "ORD": "Chicago, US",
        "OSL": "Oslo, NO",
        "PER": "Perth, AU",
        "PHL": "Philadelphia, US",
        "PHX": "Phoenix, US",
        "PRG": "Prague, CZ",
        "PVG": "Shanghai, CN",
        "SEA": "Seattle, US",
        "SFO": "San Francisco, US",
        "SIN": "Singapore, SG",
        "SLC": "Salt Lake City, US",
        "SYD": "Sydney, AU",
        "SZX": "Shenzhen, CN",
        "TLV": "Tel Aviv, IL",
        "TPE": "Taipei, TW",
        "TXL": "Berlin, DE",
        "VIE": "Vienna, AT",
        "WAW": "Warsaw, PL",
        "YTO": "Toronto, CA",
        "YUL": "Montreal, CA",
        "YVR": "Vancouver, CA",
        "ZHY": "Zhongwei, CN",
        "ZRH": "Zurich, CH",
    }
    try:
        return pop_dict[pop.upper()]
    except (RuntimeError, TypeError, NameError, KeyError):
        return "Not Found"


def concurr_f(func, xx: list, *args, **kwargs) -> list:
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        device_info = {executor.submit(func, x, *args, **kwargs): x for x in xx}
        for future in concurrent.futures.as_completed(device_info):
            _ = device_info[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                pass
    return f_result if f_result else None


@functools.lru_cache(maxsize=4)
def get_region(pop: tuple) -> str:
    """Use Jukebox API and get_nsm_region_for_site in NSM API
    to get region from AZ/PoP Locator and add to set
     """
    locator = pop
    site_code = "".join(locator)
    region = set()
    try:
        extract = "".join([l for l in site_code if l.islower()])
        region_o = nsm_isd.get_nsm_region_for_site(extract)
        if region_o:
            region.add(region_o)
        site_info = jukebox.get_site_region_details(site=site_code)
        region_t = site_info.region.realm
        if region_t:
            region.add(region_t)
    except (RuntimeError, TypeError, NameError, KeyError):
        pass
    return ",".join(region)


def get_brdr_info(args: str):
    """ Jump off method to find border devices """
    dual_verify = False
    dx_reserved = False if args.disable_reserved else True
    # PoP's below have dual-region CAR's
    dual_homed = {
        "bom51": ["bom", "sin"],
        "cdg52": ["cdg", "fra"],
        "iad21": ["corp", "iad"],
        "lhr3": ["dub", "lhr"],
        "lhr50": ["dub", "lhr"],
        "nrt4": ["nrt", "pek"],
        "nrt51": ["nrt", "pek"],
        "nrt57": ["nrt", "pek"],
        "tpe51": ["nrt", "pek"],
        "tpe52": ["nrt", "pek"],
    }
    if args.locator in dual_homed:
        args_check(
            args.locator,
            manual=True,
            d=",".join(dual_homed[args.locator]),
            dx_check=dx_reserved,
        )
        dual_verify = True
    else:
        args_check(args.locator, dx_check=dx_reserved)
    if any(l.isdigit() for l in args.locator):
        locator = args.locator
        if dual_verify:
            dual_devs_temp = collections.defaultdict(set)
            for xx in dual_homed[locator]:
                tmp = nsm.get_devices_from_nsm(args.vc_device_type, regions=xx)
                if tmp:
                    extract = {
                        devs for devs in tmp if devs.split("-")[0] == args.locator
                    }
                    if extract:
                        dual_devs_temp[xx].update(extract)
            if dual_devs_temp:
                dual_tc_car_spec(dual_devs_temp, args, regions=dual_homed[locator])
        else:
            region = get_region(tuple(locator))
            a_devs_temp = nsm.get_devices_from_nsm(args.vc_device_type, regions=region)
            a_devs = [x for x in a_devs_temp if x.split("-")[0] == args.locator]
            car_spec(a_devs, args)
    else:
        a_devs = nsm.get_devices_from_nsm(args.vc_device_type, regions=args.locator)
        car_spec(a_devs, args)


def jump_off(xx: list, args, static_region=None):
    output_dict = {}
    local_vc_devs = []
    if len(xx) >= 1:
        print()
        print(
            bcolors.WARNING
            + "The {} devices below (hardware models included alongside) will be used as a starting point for border capacity searching purposes:".format(
                args.vc_device_type
            )
            + bcolors.ENDC
        )
        for dd in sorted(xx, key=lambda x: int(x.rsplit("-", 1)[-1].split("r")[-1])):
            local_vc_devs.append(dd)
            hware_found = temp_hardware_func(dd)
            # Adding VC Hardware dict for design verification reasons
            VC_DEV_HWARE[dd] = hware_found
            print("\t{}({})".format(dd, hware_found))
        print()

        output = concurr_f(get_b_dev, xx)
        if output:
            for x in output:
                output_dict.update(x)
        temp_dict = border_filt(output_dict)
        border_srch = brdr_dev_srch(args.locator, temp_dict, region=static_region)
        print(
            bcolors.BOLD
            + "1. Beginning BR-TRA port verification for devices in {}:".format(
                args.locator
            )
            + bcolors.ENDC
        )
        border_capacity = brdr_port_cap(border_srch, hundred_gb=True)

        print(
            bcolors.WARNING
            + "\t1A. Searching for 16 * 100Gb ports on minimum of 4 BR-TRA's (400G per TRA)"
            + bcolors.ENDC
        )
        border_elig = brdr_port_verify(
            args.locator,
            border_capacity,
            tra_verify=True,
            speed=100,
            amount=4,
            threshold=4,
        )
        if not border_elig:
            print(
                bcolors.FAIL
                + "\t   Request for 16 * 100Gb ports on minimum of 4 BR-TRA's cannot be fulfilled"
                + bcolors.ENDC
            )
            print()
            print(
                bcolors.WARNING
                + "\t1B. Searching for 8 * 100Gb ports on minimum of 4 BR-TRA's (200G per TRA)"
                + bcolors.ENDC
            )
            border_elig_retry = brdr_port_verify(
                args.locator,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=2,
                threshold=4,
            )
            if not border_elig_retry:
                print(
                    bcolors.FAIL
                    + "\t   Request for 8 * 100Gb ports on minimum of 4 BR-TRA's cannot be fulfilled"
                    + bcolors.ENDC
                )
                print()
                tra_extracted = all("br-tra" in x for x in border_capacity)
                if tra_extracted:
                    print(
                        f"\tThe {len(border_capacity)} {bcolors.WARNING}BR-TRA{bcolors.ENDC} devices below were audited for available ports:"
                    )
                    for k in sorted(
                        border_capacity,
                        key=lambda x: int(x.rsplit("-", 1)[-1].split("r")[-1]),
                    ):
                        status = "FAILED"
                        print(f"\t   {k:>22s}: {bcolors.FAIL}{status}{bcolors.ENDC}")
                kct_jump_func(
                    args.locator,
                    border_capacity,
                    args.locator,
                    static_region=static_region,
                )

        if border_elig:
            print(
                bcolors.OKGREEN
                + "\t   Request for 16 * 100Gb ports on minimum of 4 BR-TRA's can be fulfilled (more information below)"
                + bcolors.ENDC
            )
            print()
            print(
                bcolors.OKGREEN
                + "\tSUCCESS! 16 * 100G - 4 diff TRAs (400G per TRA) = 1.6T (Most Preferred) - Can be fulfilled"
                + bcolors.ENDC
            )
            verified_ports(border_capacity, number=4, value="br-tra")
        elif border_elig_retry:
            print(
                bcolors.OKGREEN
                + "\t   Request for 8 * 100Gb ports on minimum of 4 BR-TRA's can be fulfilled (more information below)"
                + bcolors.ENDC
            )
            print()
            print(
                bcolors.OKGREEN
                + "\tSUCCESS! 8 * 100G - 4 diff TRAs (200G per TRA) = 800G (Secondary Option) - Can be fulfilled"
                + bcolors.ENDC
            )
            verified_ports(border_capacity, number=2, value="br-tra")
        if BR_DEVICES and local_vc_devs:
            verify_arch(tuple(BR_DEVICES), tuple(local_vc_devs), args.locator)
        if args.max_bandwidth and (BR_DEVICES and local_vc_devs):
            netvane_info(BR_DEVICES, local_vc_devs, args.locator)
        if MISC_INFO:
            p_misc_info(dict(MISC_INFO), args.locator)

    else:
        print(bcolors.FAIL + "No devices found. Exiting" + bcolors.ENDC)
        sys.exit()


def verify_arch(brd_dev: list, vc_dev: list, pop: str):
    """ Verify PoP Architecture https://w.amazon.com/bin/view/Main/Interconnect/DX_MPLSoUDP_HLD/#HVC-COR3C3EDXBackhaul """
    small_pop_sites = {"dub65", "ewr53", "gamma", "iad53", "sfo20", "sfo50"}
    cap = band_util(brd_dev, vc_dev, pop, converted=False)
    if len(cap) >= 1:
        if all("vc-dar" in c for c in cap) or VC_DAR_FOUND:
            MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add(
                "DX Small PoP"
            )
        # else:
        vc_cap = collections.defaultdict(list)
        for _, v in cap.items():
            for ae, c in v.items():
                for _, l in c.items():
                    vc_cap[ae].append(l)
        if vc_cap:
            get_design(dict(vc_cap), pop)
    else:
        MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add("Unknown")


def get_design(x: dict, pop: str):
    design_bool = {
        "Centennial": False,
        "DX Small PoP": False,
        "FreightCar": False,
        "Heimdall": False,
        "Legacy CAR": False,
        "PhoenixV1": False,
        "PhoenixV2": False,
        "Unknown": False,
    }
    # Hard coding phase1 Phoenix sites (https://w.amazon.com/bin/view/AWSDirectConnect/Phoenix/HLD/#HBorderCapacity)
    phxv1_pop = {"sfo5", "sfo50", "ewr53", "bah53", "iad66", "lax61"}
    # Hard coding FreightCar sites (https://w.amazon.com/index.php/EC2/Networking/IXOps/FreightCar)
    freightcar = {"sea4", "jfk6", "sfo20", "lhr3", "sin2", "hio50", "dub3"}
    _ = phx_cas_check(x, pop)
    for dev, b in dict(x).items():
        band = sorted(b, reverse=True)
        if band[0] != band[-1]:
            MISC_INFO["VC Devices with unequal LAG capacity distribution:"].add(dev)
        # if pop in phxv1_pop:
        #    design_bool["PhoenixV1"] = True
        if pop in freightcar:
            # Additional checks needed for sites that were never had Freightcar design implemented (example: sfo20)
            if dev in VC_DEV_HWARE:
                if "MX10003" in VC_DEV_HWARE[dev]:
                    design_bool["FreightCar"] = True
        # Adding check for Heimdall design https://w.amazon.com/bin/view/Interconnect/DirectConnect_Encryption/
        if "-v4-" in dev and dev not in VC_CAS_CHECK:
            design_bool["Heimdall"] = True
        elif "-v3-" in dev and dev not in VC_CAS_CHECK:
            design_bool["PhoenixV2"] = True
        elif "-v2-" in dev and dev not in VC_CAS_CHECK:
            design_bool["Centennial"] = True
        elif "-v1-" in dev and dev not in VC_CAS_CHECK:
            design_bool["PhoenixV1"] = True
        elif not re.findall(r"-v[1234]-", dev):
            design_bool["Legacy CAR"] = True
        # nums = majorityElement(band)
        # if 199 >= nums >= 39:
        #    design_bool["Legacy CAR"] = True

    for arch, verified in design_bool.items():
        if verified:
            MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add(arch)


def phx_cas_check(devices: dict, pop: str) -> None:
    """ This will bypass the IAD66 ByteDance CAS's (iad66-vc-cas-iad-p1-v1-r[1-8]) by design 
    since they backhaul to VC-EDG's in IAD7
    """
    output_dict_v1 = {}
    output_dict_v2 = {}
    output_dict_v3 = {}
    output_dict_v4 = {}
    versions = collections.defaultdict(list)
    phx_devices = {l for l in devices if re.findall(r"-v[1234]-", l)}
    versions = collections.defaultdict(list)
    for x in phx_devices:
        versions[x.rsplit("-")[-2]].append(x)
    for vers, devs in dict(versions).items():
        for x in devs:
            car = nsm_isd.get_raw_interfaces_for_device(x)
            get_neigh = {
                xx["neighbors"]["link_layer"]["device_name"]
                for xx in car
                if "neighbors" in xx
                if "-vc-cas-" in xx["neighbors"]["link_layer"]["device_name"]
            }
            if len(get_neigh) >= 1:
                cas_check = phx_cas_design(tuple(get_neigh))
                if vers == "v1":
                    output_dict_v1.update(cas_check)
                if vers == "v2":
                    output_dict_v2.update(cas_check)
                if vers == "v3":
                    output_dict_v3.update(cas_check)
                if vers == "v4":
                    output_dict_v4.update(cas_check)
    if output_dict_v1:
        MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add("PhoenixV1")
        phx_design_verify(output_dict_v1, pop, version="v1")
    if output_dict_v2:
        MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add("Centennial")
        phx_design_verify(output_dict_v2, pop, version="v2")
    if output_dict_v3:
        MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add("PhoenixV2")
        phx_design_verify(output_dict_v3, pop, version="v3")
    if output_dict_v4:
        MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add("Heimdall")
        phx_design_verify(output_dict_v4, pop, version="v4")
    # return output_dict


@functools.lru_cache(maxsize=12)
def phx_cas_design(s: tuple) -> dict:
    cas_count = {}
    cas_interf = collections.defaultdict(list)
    for c in s:
        cas = nsm_isd.get_raw_interfaces_for_device(c)
        for x in cas:
            intf = x["short_name"].split("-")[0]
            car_check = x["interface_description"]
            if (
                intf.startswith("ge")
                or intf.startswith("xe")
                or intf.startswith("et")
                and not "-vc-car" in car_check
            ):
                cas_interf[c].append(int(x["bandwidth_mbit"]) // 1000)

    for d, s in dict(cas_interf).items():
        agg = collections.Counter(s)
        cas_count[d] = dict(sorted(agg.items(), key=lambda x: int(x[0])))
    return cas_count


def phx_design_verify(d: dict, pop: str, version=None) -> None:
    one_s = 0
    ten_s = 0
    hun_s = 0
    for _, intf in d.items():
        if 100 in intf:
            hun_s += intf[100]
        if 10 in intf:
            ten_s += intf[10]
        if 1 in intf:
            one_s += intf[1]

    if version == "v1":
        if hun_s > 4:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("PhoenixV1 - Full (No longer deployed)")
        elif hun_s == 4:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("PhoenixV1 - Full 4 (No longer deployed)")
        else:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("PhoenixV1 - Flex (No longer deployed)")
    if version == "v2":
        if ten_s >= 1:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("Centennial Flex")
        elif ten_s == 0 and hun_s >= 1:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("Centennial (100G only)")
    if version == "v3":
        if one_s >= 1:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("Renaissance 1G-10G")
        elif one_s == 0 and ten_s >= 1:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("Renaissance 10G")
    if version == "v4":
        if one_s >= 1 or ten_s >= 1:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("Heimdall 1G-10G")
        elif ten_s >= 1 or hun_s >= 1:
            MISC_INFO[
                "Specific Phoenix design code name deployed in {}:".format(pop)
            ].add("Heimdall Flex")


# Function will be deprecated
# def majorityElement(nums: list) -> int:
#     count = 0
#     candidate = None

#     for num in nums:
#         if count == 0:
#             candidate = num
#         count += 1 if num == candidate else -1

#     return candidate


# def car_spec(xx: list, vc_type, location: str):
def car_spec(xx: list, args):
    global BR_DEVICES
    global MISC_INFO
    list_a, list_b = [], []
    for x in xx:
        if x.count("-") > 4:
            list_b.append(x)
        else:
            list_a.append(x)

    if list_a:
        jump_off(list_a, args)

        if list_b:
            BR_DEVICES.clear()
            MISC_INFO.clear()
            print()
            jump_off(list_b, args)
    if list_b and not list_a:
        jump_off(list_b, args)


def dual_tc_car_spec(x: dict, args, regions=None):
    global BR_DEVICES
    global MISC_INFO
    diff_c = 0
    values = [r for r in x]
    static = x[values[0]]
    for v in values[1:]:
        if not static == set(x[v]):
            diff_c += 1
    if diff_c >= 1:
        print(
            "Dual-homed PoP's found - below are the following region(s) that will be verified independently:"
        )
        for reg in values:
            print(f"\t{bcolors.OKGREEN}{reg}{bcolors.ENDC}")

        for region, devices in x.items():
            print()
            print(
                f"Performing backhaul verification for: {bcolors.OKGREEN}{region}{bcolors.ENDC}"
            )
            get_region = region
            jump_off(devices, args, static_region=",".join(regions))
            BR_DEVICES.clear()
            MISC_INFO.clear()
    else:
        print(
            "Dual-homed PoP's found but they contain the same devices - the region below will be verified:"
        )
        print(f"\t{bcolors.OKGREEN}{values[0]}{bcolors.ENDC}")
        get_region = values[0]
        jump_off(x[values[0]], args, static_region=",".join(regions))


def max_customer_check(device):
    p = ddb.get_device_from_table(TABLE, "Name", device)["Interfaces"]
    tally = 0
    for x in p:
        if "-vc-cas" in x["Description"].lower():
            VC_CAS_CHECK[device] = True
            MISC_INFO["VC-CAS Devices found:"].add("Yes")
            if "Neighbor" in x:
                if x["Neighbor"] not in VC_CAS_CHECK:
                    VC_CAS_CHECK[x["Neighbor"]] = True
                    max_customer_check(x["Neighbor"])
            else:
                continue
        if "customer" in x["Description"].lower():
            tally += 1
            if tally >= 155:
                # print(f"{device} - Threshold breached")
                MISC_INFO[
                    "The following customer-facing devices may exceed customer-connection threshold:"
                ].add(device)
                break


def get_b_dev(sp: str, a_dev="placeholder", b_dev="br-tra,vc-dar,vc-cor") -> dict:
    """ Retrieve list of border devices to be searched for port availability """
    try:
        # logging.debug("{} searching for {} or {}".format(sp, b_dev, a_dev))
        place_hold = False
        border_info = collections.defaultdict(set)
        a_dev_srch = [x for x in a_dev.split(",")]
        b_dev_srch = [x for x in b_dev.split(",")]
        border_devices = set()
        vc_devices = set()
        a_info = nsm_isd.get_raw_device(sp)
        get_neigh = [xx for xx in a_info["interfaces"] if "neighbors" in xx]
        for xx in get_neigh:
            if "physical" in xx["class"] and "up" in xx["admin_status"]:
                if xx["neighbors"]["link_layer"]["device_name"] is not None:
                    if any(
                        yy in xx["neighbors"]["link_layer"]["device_name"].lower()
                        for yy in b_dev_srch
                    ):
                        border_devices.add(
                            xx["neighbors"]["link_layer"]["device_name"].lower()
                        )
                    if any(
                        yy in xx["neighbors"]["link_layer"]["device_name"].lower()
                        for yy in a_dev_srch
                    ):
                        vc_devices.add(
                            xx["neighbors"]["link_layer"]["device_name"].lower()
                        )

        if "-vc-car" in sp:
            max_customer_check(sp)
            car_tra_nar_check(sp, border_devices)
        # vc_devices var maybe removed in later versions of script - adding placeholder for now
        if vc_devices:
            place_hold = True
            # for a in vc_devices:
            #     if "-vc-cas-" in a:
            #         VC_CAS_CHECK[sp] = True
            #         MISC_INFO["VC-CAS Devices found:"].add("Yes")
            #     # else:
            #    border_info[a].add("SEARCHNEEDED")

        if border_devices:
            for b in border_devices:
                border_info[sp].add(b)
        return dict(border_info)
    except Exception as e:
        FAILED_DEVICES[sp] = e


def car_tra_nar_check(car: str, brd: set):
    count = 0
    for x in brd:
        if "br-tra" in x:
            count += 1

    if count < 4:
        MISC_INFO[
            "These VC-CAR's are currently striped to less than 4 BR-TRA's (this may incur a NAR):"
        ].add(car)


def brdr_dev_srch(pop: str, x: dict, region=None) -> list:
    """ Initial border device search function that
    parses the dictionary based on border devices found in the get_b_dev
    function
    """
    b_devices = set(itertools.chain(*[l for _, l in x.items()]))
    if len(b_devices) >= 1:
        # Adding set comprehension for IAD53 split TRA/DAR scenario
        mod_b = {v for v in b_devices if "br-tra" in v or "br-kct" in v}
        extract = [
            list(g)[0]
            for k, g in itertools.groupby(mod_b, key=lambda x: x.split("-")[0])
        ]
        # Multiple Backhaul TC verification
        if not region:
            mult_tc_check = set([x.split("-")[0] for x in extract])
            if len(mult_tc_check) >= 2:
                MISC_INFO["Multiple Backhaul TC's Found - Site Locators are"].update(
                    mult_tc_check
                )
            # Multiple Backhaul Region verification
            found_region = set([nsm_isd.get_nsm_region_for_device(x) for x in extract])
            ret_region = ",".join(found_region)
            if len(found_region) >= 2:
                MISC_INFO["Multiple Backhaul TC's Found - Region Locators are"].add(
                    found_region
                )
            if pop in PIONEER_SITES:
                diff = set(PIONEER_SITES[pop]) - mult_tc_check
                found = ",".join(PIONEER_SITES[pop])
                if len(diff) >= 1:
                    MISC_INFO[
                        f"Pioneer PoP appears to be single-homed - expected TC's: {bcolors.OKGREEN}{found}{bcolors.ENDC} - missing TC(s):"
                    ].update(diff)
                    MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add(
                        "Pioneer"
                    )
        else:
            ret_region = region
        if all("br-tra" in x for x in extract):
            devices = nsm.get_devices_from_nsm("br-tra", regions=ret_region)
        elif all("br-kct" in x for x in extract):
            devices = nsm.get_devices_from_nsm("br-kct", regions=ret_region)
        if devices:
            found_devs = [
                x
                for x in devices
                if any(x.split("-")[0] == l.split("-")[0] for l in extract)
            ]
            return found_devs
        else:
            print(bcolors.FAIL + "No BR-TRA or BR-KCT devices found" + bcolors.ENDC)
    else:
        print(bcolors.FAIL + "No Border Devices Found" + bcolors.ENDC)
        sys.exit()


def brdr_port_cap(
    devices: list, ten_gb=False, forty_gb=False, hundred_gb=False
) -> dict:
    """ Returns dict of port availability info based on
    specified interface speed in function parameter
    """
    ports = {x: portdata.get_device_available_port(x) for x in devices}
    filt_ports = {k: v for k, v in ports.items() if v is not None}
    # Add to global port-availability dictionary
    if filt_ports:
        # Populate hardware device dict
        _ = concurr_f(hardware_cache, filt_ports)
        AVAIL_PORT_DICT.update(filt_ports)
    agg_border = collections.defaultdict(dict)
    for i in filt_ports:
        agg_border[i] = {}
        for x, y in filt_ports[i].items():
            count = int(x) // 1000
            if hundred_gb:
                if count == 100:
                    agg_border[i][count] = len(y)
            if forty_gb:
                if count == 40:
                    agg_border[i][count] = len(y)
            if ten_gb:
                if count == 10:
                    agg_border[i][count] = len(y)

    return dict(agg_border)


def brdr_port_verify(
    location: str,
    devices: dict,
    tra_verify=False,
    kct_verify=False,
    speed=0,
    amount=0,
    threshold=0,
) -> bool:
    """ Returns boolean for specified capacity request """
    if tra_verify:
        tra_extracted = all("br-tra" in x for x in devices)
        if not tra_extracted:
            d_type = ",".join(set([l[5:11] for l in devices]))
            print(
                f"\tNo BR-TRA devices found to be verified  - Proceeding to {bcolors.WARNING}Step 2 (BR-KCT port verification){bcolors.ENDC}"
            )
            print(f"\t   Device-type found: {bcolors.WARNING}{d_type}{bcolors.ENDC}")
            return False
    if kct_verify:
        kct_extracted = all("br-kct" in x for x in devices)
        if not kct_extracted:
            d_type = ",".join(set([l[5:11] for l in devices]))
            print(
                f"\tNo BR-KCT devices found to be verified  - Proceeding to {bcolors.WARNING}Step 3 (Interim BR-TRA port verification{bcolors.ENDC}"
            )
            print(f"\t   Device-type found: {bcolors.WARNING}{d_type}{bcolors.ENDC}")
            return False
    if tra_verify or kct_verify:
        elig_devices = set()
        PHX_TRA_ELIG = 0
        for d, i in devices.items():
            for x, v in i.items():
                if x == speed and v >= amount:
                    elig_devices.add(d)
                    PHX_TRA_ELIG += 1
                else:
                    pass

        if PHX_TRA_ELIG >= threshold:
            verify = multi_tc_verify(
                location, devices, threshold=threshold, number=amount, speed=speed
            )
            # Verify DX Ports are available after multi-TC verification
            if verify and elig_devices:
                if tra_verify and RESERVE_PORTS:
                    port_verify = dx_port_verify(
                        location,
                        tuple(elig_devices),
                        threshold=threshold,
                        number=amount,
                        speed=str(speed * 1000),
                        border="br-tra",
                    )
                    return port_verify
                else:
                    return verify
                # No port reservations found for BR-KCT devices yet
                # elif kct_verify:
                #     port_verify = dx_port_verify(
                #         location,
                #         elig_devices,
                #         threshold=threshold,
                #         number=amount,
                #         speed=str(speed * 10000),
                #         border="br-kct",
                #     )
        else:
            return False


def kct_jump_func(pop: str, devices: dict, location: str, static_region=None):
    """ Seperate jumpoff function for KCT devices to be verified
    for port availability/capacity requests
    """
    KCT_VERIFIED = False
    print()
    if VC_COR_BRICK:
        # print(
        #    bcolors.BOLD
        #    + "2. Beginning BR-KCT port verification for devices in {locate} (VC-COR devices already found in {locate}):".format(
        #        locate=location
        #    )
        #    + bcolors.ENDC
        # )
        print(
            f"{bcolors.BOLD}2. Beginning BR-KCT port verification for devices in {location} ({bcolors.ENDC}{bcolors.OKGREEN}VC-COR devices already found in {location}{bcolors.ENDC}{bcolors.BOLD}):{bcolors.ENDC}"
        )
    else:
        print(
            f"{bcolors.BOLD}2. Beginning BR-KCT port verification for devices in {location} ({bcolors.ENDC}{bcolors.WARNING}this would require deployment of VC-COR devices{bcolors.ENDC}{bcolors.BOLD}):{bcolors.ENDC}"
        )
        # print(
        #    bcolors.BOLD
        #    + "2. Beginning BR-KCT port verification for devices in {} (this would require deployment of VC-COR devices):".format(
        #        location
        #    )
        #    + bcolors.ENDC
        # )
    # If pop not in Pioneer dict then proceed to KCT port audit
    if pop not in PIONEER_SITES:
        output_kct = {}
        kct_locat = set([x for x in devices])
        if all("kct" in s for s in kct_locat):
            kct_srch = list(kct_locat)
        else:
            # output = [get_b_dev(x, a_dev="placeholder", b_dev="br-kct") for x in kct_locat]
            output = concurr_f(
                get_b_dev, list(kct_locat), a_dev="placeholder", b_dev="br-kct"
            )
            for x in output:
                output_kct.update(x)
            kct_srch = brdr_dev_srch(location, output_kct, region=static_region)
        kct_capacity = brdr_port_cap(kct_srch, ten_gb=True, forty_gb=True)
        print(
            bcolors.WARNING
            + "\t2A. Searching for 4 * 40Gb ports on minimum of 8 BR-KCT's (160G per KCT)"
            + bcolors.ENDC
        )
        kct_elig = brdr_port_verify(
            location, kct_capacity, kct_verify=True, speed=40, amount=4, threshold=8
        )
        if not kct_elig:
            print(
                bcolors.FAIL
                + "\t   Request for 4 * 40Gb ports on minimum of 8 BR-KCT's cannot be fulfilled"
                + bcolors.ENDC
            )
            print()
            print(
                bcolors.WARNING
                + "\t2B. Searching for 16 * 10Gb ports on minimum of 8 BR-KCT's (160G per KCT)"
                + bcolors.ENDC
            )
            kct_elig_retry = brdr_port_verify(
                location,
                kct_capacity,
                kct_verify=True,
                speed=10,
                amount=16,
                threshold=8,
            )
            if not kct_elig_retry:
                print(
                    bcolors.FAIL
                    + "\t   Request for 16 * 10Gb ports on minimum of 8 BR-KCT's cannot be fulfilled"
                    + bcolors.ENDC
                )
                print()
                kct_extracted = all("br-kct" in x for x in kct_capacity)
                if kct_extracted:
                    print(
                        f"\tThe {len(kct_capacity)} {bcolors.WARNING}BR-KCT{bcolors.ENDC} devices below were audited for available ports:"
                    )
                    for k in sorted(
                        kct_capacity,
                        key=lambda x: int(x.rsplit("-", 1)[-1].split("r")[-1]),
                    ):
                        status = "FAILED"
                        print(f"\t   {k:>22s}: {bcolors.FAIL}{status}{bcolors.ENDC}")
                print()
                print(
                    bcolors.FAIL
                    + "\tStandard request(s) cannot be fulfilled on BR-TRA's/KCT's.  Running interim BR-TRA port check"
                    + bcolors.ENDC
                )

        if kct_elig:
            print(
                bcolors.OKGREEN
                + "\t   Request for 4 * 40Gb ports on minimum of 8 BR-KCT's can be fulfilled (more information below)"
                + bcolors.ENDC
            )
            print()
            print(
                bcolors.OKGREEN
                + "\tSUCCESS! 4 * 40G - 8-diff KCT (160G per KCT) = 1.28T (Most Preferred) - Can be fulfilled"
                + bcolors.ENDC
            )
            verified_ports(kct_capacity, number=4, speed="40", value="br-kct")
            KCT_VERIFIED = True
        elif kct_elig_retry:
            print(
                bcolors.OKGREEN
                + "\t   Request for 16 * 10Gb ports on minimum of 8 BR-KCT's can be fulfilled (more information below)"
                + bcolors.ENDC
            )
            print()
            print(
                bcolors.OKGREEN
                + "\tSUCCESS! 16 * 10G - 8-diff KCT (160G per KCT) = 1.28T (Secondary Option) - Can be fulfilled"
                + bcolors.ENDC
            )
            verified_ports(kct_capacity, number=16, speed="10", value="br-kct")
            KCT_VERIFIED = True

        if not KCT_VERIFIED:
            interim_tra_verify(devices, location)
    else:
        print(
            f"\tINFO: {bcolors.WARNING}{pop}{bcolors.ENDC} appears to be a Pioneer PoP and this negates the BR-KCT capacity verification - Proceeding to {bcolors.WARNING}Step 3 (Interim BR-TRA port audit){bcolors.ENDC}"
        )
        interim_tra_verify(devices, location)


def get_hardware(x: dict) -> dict:
    """ Function returns dict of hardware models found """
    device_dict = {
        d: "".join(nsm.get_device_hardware_from_nsm(d)["Chassis"]) for d, _ in x.items()
    }
    return device_dict


def hardware_cache(x: str) -> str:
    try:
        r = HARDWARE_INFO[x]
    except (TypeError, KeyError):
        try:
            r = "".join(nsm.get_device_hardware_from_nsm(x)["Chassis"])
            if r:
                HARDWARE_INFO[x] = r
        except (RuntimeError, TypeError, NameError, KeyError):
            r = "NotFound"
    return r


def temp_hardware_func(x: str) -> str:
    try:
        r = "".join(nsm.get_device_hardware_from_nsm(x)["Chassis"])
    except (RuntimeError, TypeError, NameError, KeyError):
        if x.count("-") > 4:
            r = "JNP10003 [MX10003]"
        else:
            r = "MX960"
    return r


def dar_version(x: str) -> str:
    try:
        r = "".join(nsm.get_device_hardware_from_nsm(x)["Chassis"])
        extract_dig = len([l for l in r if l.isdigit()])
        if extract_dig > 4:
            return "VC-DARv2"
        else:
            return "VC-DARv1"
    except (RuntimeError, TypeError, NameError, KeyError):
        return "VC-DAR version not found"


def verified_ports(d: dict, number=0, speed="100", value="br-tra"):
    """ Function prints port availability and speed information """
    print()
    elig_port_info = {d: v for d, v in d.items() for x, y in v.items() if y >= number}
    # hardware_info = get_hardware(elig_port_info)
    if "br-tra" in value:
        tra_version(elig_port_info)
    if "br-kct" in value:
        kct_version(elig_port_info)
    print(
        bcolors.BOLD
        + "\tPort information for {} devices that meet capacity request".format(value)
        + bcolors.ENDC
    )
    for a, b in sorted(
        elig_port_info.items(),
        key=lambda x: int(x[0].rsplit("-", 1)[-1].split("r")[-1]),
    ):
        for aa, bb in b.items():
            if speed == str(aa):
                if int(bb) >= number:
                    print(
                        "\t   {:>22}({}) - Number of {}Gb ports found: {}".format(
                            a, HARDWARE_INFO[a], aa, bb
                        )
                    )


def kct_version(h_ware: dict):
    kctv_bool = {
        "KCTv3": False,
        "KCTv2": False,
        "KCTv1": False,
    }
    for d in h_ware:
        if "PTX" in HARDWARE_INFO[d]:
            kctv_bool["KCTv3"] = True
        elif "QFX1000" in HARDWARE_INFO[d]:
            kctv_bool["KCTv2"] = True
        else:
            kctv_bool["KCTv1"] = True

    for arch, verified in kctv_bool.items():
        if verified:
            MISC_INFO["KCT Architecture version(s) found:"].add(arch)


def tra_version(h_ware: dict):
    for d in h_ware:
        if "PTX" in HARDWARE_INFO[d]:
            MISC_INFO["PTX BR-TRA's found:"].add("Yes")
        if "MX" in HARDWARE_INFO[d]:
            MISC_INFO["MX BR-TRA's found:"].add("Yes")


@functools.lru_cache(maxsize=12)
def port_adhere(sp: str) -> bool:
    """ Verify if PTX TRA's are adhering to port allocation standards -- if not then any ports can be used """
    dx_tra_ptx = range(36, 48)
    dev = nsm_isd.get_raw_interfaces_for_device(sp)
    get_neigh = [
        (
            xx["short_name"],
            xx["bandwidth_mbit"],
            xx["neighbors"]["link_layer"]["device_name"],
        )
        for xx in dev
        if "neighbors" in xx
        if "/" in xx["short_name"]
    ]
    ports = sorted(get_neigh, key=lambda x: int(x[0].split("/")[2].split(":")[0]))
    found = [
        l[0]
        for l in ports
        if "vc-dar" in l[2] or "vc-car" in l[2]
        if int(l[0].split("/")[2].split(":")[0]) not in dx_tra_ptx
    ]
    if len(found) > 2:
        return False
    else:
        return True


@functools.lru_cache(maxsize=128)
def dx_port_verify(
    pop: str, devices: tuple, threshold=0, number=0, speed=0, border=None
) -> bool:
    """ Using port mappings in https://w.amazon.com/bin/view/Networking/IS/Design/BR-TRA/ """
    print(
        f"\t   Adequate ports found on {border} devices: {bcolors.OKGREEN}YES{bcolors.ENDC}"
    )
    good_dev = set()
    bad_dev = set()
    tally = 0
    dx_tra_mx = range(0, 4)
    dx_tra_ptx = range(36, 48)
    if "br-tra" == border:
        for d in sorted(devices):
            if "PTX" in HARDWARE_INFO[d]:
                if not port_adhere(d):
                    print(
                        f"\t      {bcolors.WARNING}Skipping DX-reserved port checks on: {bcolors.FAIL}{d}{bcolors.ENDC} (doesn't appear to follow PTX {border} port allocation standard){bcolors.ENDC}"
                    )
                    count = number + 1
                elif all(":" in e for e in AVAIL_PORT_DICT[d][speed]):
                    count = len(
                        [
                            l
                            for l in AVAIL_PORT_DICT[d][speed]
                            if int(l.split("/")[2].split(":")[0]) in dx_tra_ptx
                        ]
                    )
                else:
                    count = len(
                        [
                            l
                            for l in AVAIL_PORT_DICT[d][speed]
                            if int(l.split("/")[2]) in dx_tra_ptx
                        ]
                    )
                if count >= number:
                    tally += 1
                    good_dev.add(d)
                else:
                    bad_dev.add(d)

            elif "MX" in HARDWARE_INFO[d]:
                count = len(
                    [
                        l
                        for l in AVAIL_PORT_DICT[d][speed]
                        if int(l.split("/")[0].split("-")[1]) in dx_tra_mx
                    ]
                )
                if count >= number:
                    tally += 1
                    good_dev.add(d)
                else:
                    bad_dev.add(d)
    # No port allocations found for KCT devices

    if threshold > tally:
        print(
            f"\t   Adequate DX-reserved ports found on {border} devices: {bcolors.FAIL}NO{bcolors.ENDC}"
        )
        if good_dev and bad_dev:
            dev_port_info(a=good_dev, b=bad_dev)
        else:
            dev_port_info(b=bad_dev)
        return False
    else:
        print(
            f"\t   Adequate DX-reserved ports found on {border} devices: {bcolors.OKGREEN}YES{bcolors.ENDC}"
        )
        return True


def dev_port_info(a=None, b=None):
    if a:
        good_dev = ", ".join(a)
        print(
            f"\t      Adequate DX-reserved ports found on devices: {bcolors.OKGREEN}{good_dev}{bcolors.ENDC}"
        )
    if b:
        bad_dev = ", ".join(b)
        print(
            f"\t      Adequate DX-reserved ports NOT found on devices: {bcolors.FAIL}{bad_dev}{bcolors.ENDC}"
        )


def multi_tc_verify(pop: str, devices: dict, threshold=0, number=0, speed=0) -> bool:
    """ Function verifies if more than one TC is providing backhaul and
    will verify if backhaul devices in the TC's meet threshold for capacity
    requests
    Reference URLs below for more information:
    https://code.amazon.com/packages/JukeboxRouterConfiguratorTemplates/blobs/mainline/--/templates/macros/pioneer-pops-info.ftl
    https://code.amazon.com/packages/JukeboxRouterConfiguratorTemplates/blobs/mainline/--/templates/macros/dx-small-pops.ftl
    """
    verified = True
    tc_count = set([c.split("-")[0] for c in devices])
    if len(tc_count) > 1:
        extract_info = {
            d: v
            for d, v in devices.items()
            for x, y in v.items()
            if y >= number and x == speed
        }
        extract = [xx for xx, yy in extract_info.items() if yy]
        tc_tally = collections.defaultdict(list)
        for devices in extract:
            tc_tally[devices.split("-")[0]].append(devices)
        if len(dict(tc_tally)) > 1:
            # Adding check for Pioneer design (if no VC-DAR found)
            if not VC_DAR_FOUND and pop in PIONEER_SITES:
                MISC_INFO["Current PoP Architecture(s) for {}:".format(pop)].add(
                    "Pioneer"
                )
            verified = all(len(x) >= threshold for y, x in tc_tally.items())
        else:
            verified = False
    return verified


def dar_tc_verify(s: dict) -> None:
    info_dict = collections.defaultdict(dict)
    dar_count = {
        y.split("-")[0] for l in s for x, v in l.items() for y in v if not "vc-dar" in y
    }
    for x in s:
        for dar, back in x.items():
            border_dev = ",".join({l.split("-")[0] for l in back if not "vc-dar" in l})
            if any("vc-dar" in b for b in back):
                info_dict[dar]["Crosslink"] = "Yes"
            if dar_count:
                if len(dar_count) < 2:
                    info_dict[dar]["Homing"] = "Single"
                elif len(dar_count) >= 2:
                    info_dict[dar]["Homing"] = "Multi"
                info_dict[dar]["Parent-TC's"] = border_dev

    for x, y in dict(info_dict).items():
        if y["Homing"] == "Single" and y["Crosslink"] == "Yes":
            MISC_INFO[
                f"VC-DAR appears to be single-homed - VC-DAR: {bcolors.FAIL}{x}{bcolors.ENDC} Crosslink Found: {bcolors.OKGREEN}Yes{bcolors.ENDC} - Parent TC found:"
            ].add(y["Parent-TC's"])
        elif y["Homing"] == "Single" and y["Crosslink"] == "NO":
            MISC_INFO[
                f"VC-DAR appears to be single-homed - VC-DAR: {bcolors.FAIL}{x}{bcolors.ENDC} Crosslink Found: {bcolors.FAIL}No{bcolors.ENDC} - Parent TC found:"
            ].add(y["Parent-TC's"])
        elif y["Homing"] == "Multi":
            MISC_INFO[
                f"VC-DAR appears to be multi-homed - VC-DAR: {bcolors.OKGREEN}{x}{bcolors.ENDC} - Parent TC(s) found:"
            ].add(y["Parent-TC's"])

    # for d, bkhaul in s.items():
    #     tc_check = [l.split("-")[0] for l in bkhaul]
    #     if len(tc_check) < 2:
    #         MISC_INFO[
    #             f"VC-DAR appears to be single-homed - VC-DAR: {bcolors.FAIL}{d}{bcolors.ENDC} - TC found:"
    #         ].update(tc_check)
    #     else:
    #         MISC_INFO[
    #             f"VC-DAR appears to be dual-homed - VC-DAR: {bcolors.OKGREEN}{d}{bcolors.ENDC} - TC(s) found:"
    #         ].update(tc_check)


def border_filt(o: dict) -> dict:
    """ Add filter search for vc-dar and vc-cor devices """
    global VC_COR_BRICK
    global VC_DAR_FOUND
    ALL_TRA = False
    new_dict = {}
    # Add BR-TRA's to set for NetVane verification
    tra_add = [y for x, y in o.items() if all("br-tra" in xx for xx in y)]
    if tra_add:
        ALL_TRA = True
        tra_final = list(set().union(*tra_add))
        for e in tra_final:
            BR_DEVICES.add(e)
    extract = set(
        [xx for x, y in o.items() for xx in y if "vc-dar" in xx or "vc-cor" in xx]
    )
    if extract:
        print(
            bcolors.WARNING
            + "Additional devices need to be searched for border capacity information. Devices below will be searched:"
            + bcolors.ENDC
        )
        for e in extract:
            if "vc-dar" in e:
                VC_DAR_FOUND = True
                if not ALL_TRA:
                    BR_DEVICES.add(e)
                MISC_INFO["VC-DAR's Found - devices found:"].add(e)
                MISC_INFO["VC-DAR Version Found:"].add(dar_version(e))
            print(
                "\t{}({})".format(
                    e, "".join(nsm.get_device_hardware_from_nsm(e)["Chassis"])
                )
            )
        print()
        # for d in extract:
        # del o[d]
        new_dict.update(o)
        if any("vc-dar" in x for x in extract):
            remain_devices = set()
            result = concurr_f(
                get_b_dev,
                [w for w in extract if "vc-dar" in w],
                a_dev="placeholder",
                b_dev="vc-cor,vc-dar,br-tra,br-kct",
            )
            if result:
                dar_tc_verify(result)
                for x in result:
                    for xx, yy in x.items():
                        if any("vc-cor" in cor for cor in yy):
                            VC_COR_BRICK = True
                            remain_devices = {cc for cc in yy if "vc-cor" in cc}
                            if remain_devices:
                                for cr in remain_devices:
                                    MISC_INFO[
                                        "VC-COR Brick Found - devices found:"
                                    ].add(cr)
                        elif any("br-tra" in y or "br-kct" in y for y in yy):
                            # Will be removed after verification
                            # dar_tc_verify(x)
                            new_dict.update(x)
            if remain_devices:
                retry = concurr_f(
                    get_b_dev,
                    remain_devices,
                    a_dev="placeholder",
                    b_dev="br-tra,br-kct",
                )
                if retry:
                    for x in retry:
                        for xx, yy in x.items():
                            # if "br-tra" in yy or "br-kct" in yy:
                            if any("br-tra" in y or "br-kct" in y for y in yy):
                                new_dict.update(x)
        if any("vc-cor" in x for x in extract):
            remain_devices = set()
            result = concurr_f(
                get_b_dev,
                [w for w in extract if "vc-cor" in w],
                a_dev="placeholder",
                b_dev="br-tra,br-kct",
            )
            if result:
                for x in result:
                    for xx, yy in x.items():
                        if (
                            any("br-tra" in y or "br-kct" in y for y in yy)
                            and "vc-cor" in xx
                        ):
                            VC_COR_BRICK = True
                            new_dict.update(x)
                            BR_DEVICES.add(xx)
                            MISC_INFO["VC-COR Brick Found - devices found:"].add(xx)

    return new_dict if new_dict else o


def interim_tra_verify(border_capacity: dict, location: str):
    """ Function verifies if any BR-TRA's can meet port-avail/capacity requests for an
    interim solution
    """
    print()
    print(
        bcolors.BOLD
        + "3. Beginning interim search for BR-TRA ports since previous BR-TRA/KCT searches have failed - THIS IS A TEMPORARY SOLUTION:"
        + bcolors.ENDC
    )
    verified = False
    tra_extracted = all("br-tra" in x for x in border_capacity)
    if tra_extracted:
        while not verified:
            # print()
            # print(
            #     bcolors.BOLD
            #     + "3. Beginning interim search for BR-TRA ports since previous BR-TRA/KCT searches have failed - THIS IS A TEMPORARY SOLUTION:"
            #     + bcolors.ENDC
            # )
            print(
                bcolors.WARNING
                + "\t3A. Searching for 12 * 100Gb ports on minimum of 2 BR-TRA's (600G per TRA)"
                + bcolors.ENDC
            )
            time.sleep(0.4)
            border_elig_a = brdr_port_verify(
                location,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=6,
                threshold=2,
            )
            if not border_elig_a:
                print(
                    bcolors.WARNING
                    + "\t   12 * 100Gb ports requirement not fulfilled - Moving onto next search criteria"
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "\t   12 * 100Gb ports requirement fulfilled - SUCCESS (more information below)"
                    + bcolors.ENDC
                )
                print()
                print(
                    bcolors.OKGREEN
                    + "\tSUCCESS! 12 * 100G - 2 diff TRAs (600G per TRA) = 1.2T - Can be fulfilled"
                    + bcolors.ENDC
                )
                print(
                    bcolors.FAIL
                    + "\t   NOTE: This striping configuration (2 BR-TRA's) may incur a NAR since less than 4 BR-TRA's are being striped to"
                    + bcolors.ENDC
                )
                verified_ports(border_capacity, number=6, value="br-tra")
                verified = True
                break

            print(
                bcolors.WARNING
                + "\t3B. Running TRA port audit for 8 * 100Gb ports on minimum of 4 BR-TRA's (200G per TRA)"
                + bcolors.ENDC
            )
            time.sleep(0.4)
            border_elig_b = brdr_port_verify(
                location,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=2,
                threshold=4,
            )
            if not border_elig_b:
                print(
                    bcolors.WARNING
                    + "\t   8 * 100Gb ports requirement not fulfilled - Moving onto next search criteria"
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "\t   8 * 100Gb ports requirement fulfilled - SUCCESS (more information below)"
                    + bcolors.ENDC
                )
                print()
                print(
                    bcolors.OKGREEN
                    + "\tSUCCESS! 8 * 100G - 4 diff TRAs (200G per TRA) = 800G - Can be fulfilled"
                    + bcolors.ENDC
                )
                verified_ports(border_capacity, number=2, value="br-tra")
                verified = True
                break

            print(
                bcolors.WARNING
                + "\t3C. Running TRA port audit for 6 * 100Gb ports on minimum of 3 BR-TRA's (200G per TRA)"
                + bcolors.ENDC
            )
            time.sleep(0.4)
            border_elig_c = brdr_port_verify(
                location,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=2,
                threshold=3,
            )
            if not border_elig_c:
                print(
                    bcolors.WARNING
                    + "\t   6 * 100Gb ports requirement not fulfilled - Moving onto next search criteria"
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "\t   6 * 100Gb ports requirement fulfilled - SUCCESS (more information below)"
                    + bcolors.ENDC
                )
                print()
                print(
                    bcolors.OKGREEN
                    + "\tSUCCESS! 6 * 100G - 3 diff TRAs (200G per TRA) = 600G - Can be fulfilled"
                    + bcolors.ENDC
                )
                print(
                    bcolors.FAIL
                    + "\t   NOTE: This striping configuration (3 BR-TRA's) may incur a NAR since less than 4 BR-TRA's are being striped to"
                    + bcolors.ENDC
                )
                verified_ports(border_capacity, number=2, value="br-tra")
                verified = True
                break

            print(
                bcolors.WARNING
                + "\t3D. Running TRA port audit for 8 * 100Gb ports on minimum of 2 BR-TRA's (400G per TRA)"
                + bcolors.ENDC
            )
            time.sleep(0.4)
            border_elig_d = brdr_port_verify(
                location,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=4,
                threshold=2,
            )
            if not border_elig_d:
                print(
                    bcolors.WARNING
                    + "\t   8 * 100Gb ports requirement not fulfilled - Moving onto next search criteria"
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "\t   8 * 100Gb ports requirement fulfilled - SUCCCESS (more information below)"
                    + bcolors.ENDC
                )
                print()
                print(
                    bcolors.OKGREEN
                    + "\tSUCCESS! 8 * 100G - 2 diff TRAs (400G per TRA) = 800G - Can be fulfilled"
                    + bcolors.ENDC
                )
                print(
                    bcolors.FAIL
                    + "\t   NOTE: This striping configuration (2 BR-TRA's) may incur a NAR since less than 4 BR-TRA's are being striped to"
                    + bcolors.ENDC
                )
                verified_ports(border_capacity, number=4, value="br-tra")
                verified = True
                break

            print(
                bcolors.WARNING
                + "\t3E. Running TRA port audit for 4 * 100Gb ports on minimum of 4 BR-TRA's (100G per TRA)"
                + bcolors.ENDC
            )
            time.sleep(0.4)
            border_elig_e = brdr_port_verify(
                location,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=1,
                threshold=4,
            )
            if not border_elig_e:
                print(
                    bcolors.WARNING
                    + "\t   4 * 100Gb ports requirement not fulfilled - Moving onto next search criteria"
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "\t   4 * 100Gb ports requirement fulfilled - SUCCESS (more information below)"
                    + bcolors.ENDC
                )
                print()
                print(
                    bcolors.OKGREEN
                    + "\tSUCCESS! 4 * 100G - 4 diff TRAs (100G per TRA) = 400G - Can be fulfilled"
                    + bcolors.ENDC
                )
                verified_ports(border_capacity, number=1, value="br-tra")
                verified = True
                break

            print(
                bcolors.WARNING
                + "\t3F. Running TRA port audit for 4 * 100Gb ports on minimum of 2 BR-TRA's (200G per TRA)"
                + bcolors.ENDC
            )
            time.sleep(0.4)
            border_elig_f = brdr_port_verify(
                location,
                border_capacity,
                tra_verify=True,
                speed=100,
                amount=2,
                threshold=2,
            )
            if not border_elig_f:
                print(
                    bcolors.WARNING
                    + "\t   4 * 100Gb ports requirement not fulfilled - Moving onto next search criteria"
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "\t   4 * 100Gb ports requirement fulfilled - SUCCESS (more information below)"
                    + bcolors.ENDC
                )
                print()
                print(
                    bcolors.OKGREEN
                    + "\tSUCCESS! 4 * 100G - 2 diff TRAs (200G per TRA) = 400G - Can be fulfilled"
                    + bcolors.ENDC
                )
                print(
                    bcolors.FAIL
                    + "\t   NOTE: This striping configuration (2 BR-TRA's) may incur a NAR since less than 4 BR-TRA's are being striped to"
                    + bcolors.ENDC
                )
                verified_ports(border_capacity, number=2, value="br-tra")
                verified = True
                break
            print(
                bcolors.FAIL
                + "\tNo interim ports could be found on BR-TRA's"
                + bcolors.ENDC
            )
            break
    else:
        d_type = ",".join(set([l[5:11] for l in border_capacity]))
        print(
            f"\tNo BR-TRA devices found to be verified  - Proceeding to {bcolors.WARNING}Exiting port availability audit steps{bcolors.ENDC}"
        )
        print(f"\t   Device-type found: {bcolors.WARNING}{d_type}{bcolors.ENDC}")


def humanbytes(B: int) -> str:
    "Return the given bits as a human friendly KB, MB, GB, or TB string"
    b = float(B)
    Kb = float(1024)
    Mb = float(Kb ** 2)  # 1,048,576
    Gb = float(Kb ** 3)  # 1,073,741,824
    Tb = float(Kb ** 4)  # 1,099,511,627,776

    if b < Kb:
        return "{0} {1}".format(b, "Byte" if 0 == b > 1 else "Bytes")
    elif Kb <= b < Mb:
        return "{0:.2f} Kb".format(b / Kb)
    elif Mb <= b < Gb:
        return "{0:.2f} Mb".format(b / Mb)
    elif Gb <= b < Tb:
        return "{0:.2f} Gb".format(b / Gb)
    elif Tb <= b:
        return "{0:.2f} Tb".format(b / Tb)


@functools.lru_cache(maxsize=128)
def backhaul_band(
    b_devs: list, v_devs: list, pop: str, b_type="br-tra", v_type="vc-car"
) -> dict:
    try:
        border_dict = border_port_alloc.TRA_Allocation(
            pop=pop,
            vc_devices=",".join(v_devs),
            border_devices=",".join(b_devs),
            vc_device_type=v_type,
            border_device_type=b_type,
        )
        border_dict.get_car_backhaul_band(lag_check="border")
        return border_dict.existing_band_ae_per_vc
    except:
        pass


def band_util(b_devs: list, v_devs: list, pop: str, converted=False) -> dict:
    """ Function to extract backhaul capacity per AE for bandwidth utilization measurements"""
    # Need to send tuple's to LRU Cache decorator for proper useage
    b_devs = tuple(b_devs)
    v_devs = tuple(v_devs)
    backhaul_dict = collections.defaultdict(dict)
    if all("br-tra" in x for x in b_devs):
        tra_dict = backhaul_band(b_devs, v_devs, pop)
        if tra_dict:
            for b, v in tra_dict.items():
                for vv, bb in v.items():
                    backhaul_dict[b][vv] = {}
                    backhaul_dict[b][vv][bb[1]] = (
                        1073741824 * bb[0] if converted else bb[0]
                    )
    elif all("vc-dar" in x for x in b_devs):
        dar_dict = backhaul_band(b_devs, v_devs, pop, b_type="vc-dar", v_type="vc-car")
        if dar_dict:
            for b, v in dar_dict.items():
                for vv, bb in v.items():
                    backhaul_dict[b][vv] = {}
                    backhaul_dict[b][vv][bb[1]] = (
                        1073741824 * bb[0] if converted else bb[0]
                    )
    elif all("vc-cor" in x for x in b_devs):
        cor_dict = backhaul_band(b_devs, v_devs, pop, b_type="vc-cor", v_type="vc-car")
        if cor_dict:
            for b, v in cor_dict.items():
                for vv, bb in v.items():
                    backhaul_dict[b][vv] = {}
                    backhaul_dict[b][vv][bb[1]] = (
                        1073741824 * bb[0] if converted else bb[0]
                    )
    return backhaul_dict


def netvane_info(a: set, b: list, location: str):
    """ Function utilizes Netvane module that Riaz onboarded """
    if len(a) >= 1 and len(b) >= 1:
        print()
        wk_ago = datetime.timedelta(days=7)
        w = datetime.date.today() - wk_ago
        if len(a) >= 5:
            print(
                bcolors.BOLD
                + "Attempting to gather Netvane information from {} devices. To avoid rate-limiting this may take some time".format(
                    len(a)
                )
                + bcolors.ENDC
            )
        else:
            print(
                bcolors.BOLD
                + "Attempting to gather Netvane information from {} devices".format(
                    len(a)
                )
                + bcolors.ENDC
            )
        print(
            bcolors.WARNING
            + "[EXTRA] Searching for weekly MAX bandwidth usage for DX devices in {} (date-range: {} ({}) - {} ({}))".format(
                location,
                w,
                w.strftime("%A"),
                datetime.date.today(),
                datetime.date.today().strftime("%A"),
            )
            + bcolors.ENDC
        )
        util = band_util(list(a), b, location, converted=True)
        cap = netvane.get_interfaces_traffic_max_week(list(a), element_regex="^(ae)")
        filt = [x for x in cap for v in b if v in x["Description"].lower()]
        srt_vane = sorted(filt, key=lambda x: int(x["Value"]), reverse=True)
        if srt_vane:
            print(
                bcolors.BOLD
                + "\t** LAG NUMBERS ARE FROM THE BORDER DEVICES PERSPECTIVE **"
                + bcolors.ENDC
            )
            for x in srt_vane:
                for v in b:
                    if v.lower() in x["Description"].lower():
                        if not "." in x["Interface"]:
                            if "ifTrafficIn" in x["Metric"]:
                                try:
                                    print(
                                        "\t{}  --{}-->  {}".format(
                                            v, x["Interface"], x["Device_Name"]
                                        )
                                    )
                                    print(
                                        bcolors.OKGREEN
                                        + "\t\t{} out of {}".format(
                                            humanbytes(x["Value"]),
                                            humanbytes(
                                                util[x["Device_Name"]][v][
                                                    x["Interface"]
                                                ]
                                            ),
                                        )
                                        + bcolors.ENDC
                                    )
                                except KeyError:
                                    print(
                                        bcolors.FAIL
                                        + "\t\t{} - Interface Capacity Not Found (AE Not Found in hashtable)".format(
                                            humanbytes(x["Value"]),
                                        )
                                        + bcolors.ENDC
                                    )
                            elif "ifTrafficOut" in x["Metric"]:
                                try:
                                    print(
                                        "\t{}  <--{}--  {}".format(
                                            v, x["Interface"], x["Device_Name"]
                                        )
                                    )
                                    print(
                                        bcolors.OKGREEN
                                        + "\t\t{} out of {}".format(
                                            humanbytes(x["Value"]),
                                            humanbytes(
                                                util[x["Device_Name"]][v][
                                                    x["Interface"]
                                                ]
                                            ),
                                        )
                                        + bcolors.ENDC
                                    )
                                except KeyError:
                                    print(
                                        bcolors.FAIL
                                        + "\t\t{} - Interface Capacity Not Found (AE Not Found in hashtable)".format(
                                            humanbytes(x["Value"]),
                                        )
                                        + bcolors.ENDC
                                    )
        else:
            print(
                bcolors.FAIL
                + "Netvane information pertaining to devices in {} could not be found. Exiting".format(
                    location
                )
                + bcolors.ENDC
            )


def p_misc_info(x: dict, location: str):
    print()
    print(
        f"{bcolors.WARNING}[EXTRA]{bcolors.ENDC} Miscellaneous Information related to PoP/TC {bcolors.WARNING}{location}{bcolors.ENDC}:"
    )
    for info, details in sorted(x.items(), key=lambda k: len(k[1])):
        x = ", ".join(details)
        if "Multiple Backhaul TC's Found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "VC-COR Brick Found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "VC-DAR's Found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "Current PoP Architecture" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "Specific Phoenix design code name deployed in" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "KCT Architecture version" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "PTX BR-TRA's found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "MX BR-TRA's found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "VC Devices with unequal LAG capacity distribution" in info:
            print(f"\t{info} {bcolors.FAIL}{x}{bcolors.ENDC}")
        if "VC-CAS Devices found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "VC-DAR Version Found" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if "Pioneer PoP appears to be single-homed" in info:
            print(f"\t{info} {bcolors.FAIL}{x}{bcolors.ENDC}")
        if "VC-DAR appears to be single-homed" in info:
            print(f"\t{info} {bcolors.FAIL}{x}{bcolors.ENDC}")
        if "These VC-CAR's are currently striped to less than" in info:
            print(f"\t{info} {bcolors.FAIL}{x}{bcolors.ENDC}")
        if "VC-DAR appears to be multi-homed" in info:
            print(f"\t{info} {bcolors.OKGREEN}{x}{bcolors.ENDC}")
        if (
            "The following customer-facing devices may exceed customer-connection threshold"
            in info
        ):
            print(f"\t{info} {bcolors.FAIL}{x}{bcolors.ENDC}")


def main():
    global RESERVE_PORTS
    intro_message()
    now_time = datetime.datetime.now()
    args = parse_args()
    if args:
        if args.disable_reserved:
            RESERVE_PORTS = False
        get_brdr_info(args)
    finish_time = datetime.datetime.now()
    duration = finish_time - now_time
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


