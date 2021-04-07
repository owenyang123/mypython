#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
""" Brief python script compares interface description information to LLDP information
retrieved from NSM.  Example of usage is below:

/apollo/env/DXDeploymentTools/bin/cable_error_verify.py -r "pdx" -d "vc-car" -s "br-tra" #search vc-car devices for possible cabling issues with br-tra devices in PDX
/apollo/env/DXDeploymentTools/bin/cable_error_verify.py -l "nrt4" -d "vc-car" -s "br-tra" #search vc-car devices for possible cabling issues with br-tra devices in NRT4 PoP
/apollo/env/DXDeploymentTools/bin/cable_error_verify.py -r "sin" -d "br-tra" -s "vc-car" #search br-tra devices for possible cabling issues with vc-car devices in SIN
/apollo/env/DXDeploymentTools/bin/cable_error_verify.py -l "nrt12" -d "vc-edg" -s "br-agg" #search br-agg devices for possible cabling issues with vc-edge devices in NRT12 AZ
"""

import argparse
import collections
import concurrent.futures
import itertools
import json
import logging
import signal
import sys
import textwrap

from pygments import formatters, highlight, lexers

import tqdm
from dxd_tools_dev.modules import jukebox, nsm
from isd_tools_dev.modules import nsm as nsm_isd

# Enables quick termination of script if needed
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',

DEVICE_INTER = False
FAILED_DEVICES = {}

logging.basicConfig(level=logging.CRITICAL)
logging.debug("Logging Enabled")


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


def parse_args() -> str:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
    Script verifies Un-equal LAGs on VC/BR devices
    """
        ),
    )
    p.add_argument(
        "-r",
        "--region",
        help="Specify region",
        # default=False,
    )
    p.add_argument(
        "-l",
        "--locator",
        help="Specify PoP or AZ",
        # default=False,
    )
    p.add_argument(
        "-d",
        "--device",
        help="Specify device type (example: vc-car, br-tra, br-agg)",
        type=str,
        nargs="?",
        default="vc-car",
        required=True,
    )
    p.add_argument(
        "-s",
        "--search",
        help="Specify device type that you want to search for in interface description/LLDP info",
        type=str,
        nargs="?",
        default="br-tra",
        required=True,
    )
    return p.parse_args()


def rundown(args):
    print()
    print(
        bcolors.WARNING + "Starting Cable Mismatch Verification script:" + bcolors.ENDC
    )
    print(
        "\t1. Find all {} devices in {}".format(
            args.device, args.region or args.locator
        )
    )
    print(
        "\t2. Search for {} and {} intersections in {}".format(
            args.device, args.search, args.region or args.locator
        )
    )
    print(
        "\t3. Compare interface description and LLDP neighbor information for all {} devices found on {} devices".format(
            args.search, args.device
        )
    )
    print(
        "\t4. Show all interface description/LLDP neighbor mismatches (if found) between {} devices and {} devices in {}".format(
            args.device, args.search, args.region or args.locator
        )
    )
    print(
        "\t5. Show all devices that have error(s) when extracting neighbor information"
    )


def jsonify(args: dict):
    formatted_json = json.dumps(args, sort_keys=True, indent=4, separators=(",", ": "))
    colorful_json = highlight(
        formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()
    )
    print(colorful_json)


def get_lag_br(sp: str, dev_type="br-tra") -> (dict, bool):
    global DEVICE_INTER
    try:
        DIFF_FOUND = False
        device_band = collections.defaultdict(list)
        no_err = collections.defaultdict(set)
        interfaces = nsm_isd.get_raw_device(sp)
        pre_agg_links = [
            xx
            for xx in interfaces["interfaces"]
            if "physical" in xx["class"]
            and "up" in xx["admin_status"]
            and dev_type in xx["interface_description"].lower()
        ]
        phys_links = [x for x in pre_agg_links if "neighbors" in x]
        if phys_links:
            device_info = [
                (
                    xx["bandwidth_mbit"],
                    xx["name"],
                    xx["aggregation"]["name"],
                    "".join(
                        [
                            l
                            for l in xx["interface_description"].lower().split(" ")
                            if dev_type in l
                        ]
                    ),
                    xx["neighbors"]["link_layer"]["device_name"].lower(),
                    xx["neighbors"]["link_layer"]["interface_name"].lower(),
                )
                for xx in phys_links
                if dev_type in xx["interface_description"].lower()
            ]
            if device_info:
                DEVICE_INTER = True
                for xx in device_info:
                    if xx[3] != xx[4]:
                        DIFF_FOUND = True
                        speed = "Capacity: {}Gb".format(int(int(xx[0]) / 1000))
                        interface = "Interface: {}".format(xx[1])
                        lag = "AE#: {}".format(xx[2])
                        descrip = "Interface Description: {}".format(xx[3])
                        lldp_descrip = "LLDP Neighbor: {}".format(xx[4])
                        lldp_intf = "LLDP Neighbor Interface: {}".format(xx[5])
                        device_band[sp].append(
                            [speed, interface, lag, descrip, lldp_descrip, lldp_intf]
                        )
                    else:
                        if xx[4] and not DIFF_FOUND:
                            no_err[sp].add(xx[4])
            else:
                device_band[sp].append("No neighbor information found")
        if device_band and DIFF_FOUND:
            return dict(device_band), DIFF_FOUND
        else:
            return dict(no_err), DIFF_FOUND
    except Exception as e:
        FAILED_DEVICES[sp] = e
        # print(e)


def get_region(pop: str) -> str:
    """Use Jukebox API to get region from AZ/PoP Locator
        Thanks to anudeept@ for this tip
        """
    locator = pop
    site_code = locator
    site_info = jukebox.get_site_region_details(site=site_code)
    region = site_info.region.realm
    return region if region else "bah"  # small region that is a placeholder for now


def concurr_f(func, xx: list, *args, **kwargs) -> list:
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(func, x, *args, **kwargs): x for x in xx}
        kwrgs = {
            "total": len(futures),
            "unit": "nap",
            "unit_scale": True,
            "leave": True,
        }

        for f in tqdm.tqdm(concurrent.futures.as_completed(futures), **kwrgs):
            _ = futures[f]
            try:
                f_result.append(f.result())
            except Exception as e:
                pass
    return f_result if f_result else None


def kickoff_func(args):
    if args.locator:
        if any(l.isdigit() for l in args.locator):
            hash_locator = hash(args.locator)
        else:
            print(
                bcolors.FAIL
                + "No numeric identifier found in {} - Exiting".format(args.locator)
                + bcolors.ENDC
            )
            sys.exit()
        if args.region:
            t_devices = nsm.get_devices_from_nsm(args.device, regions=args.region)
        else:
            t_devices = nsm.get_devices_from_nsm(
                args.device, regions=get_region(args.locator)
            )
        devices = [x for x in t_devices if hash_locator == hash(x.split("-")[0])]
    if args.region and not args.locator:
        devices = nsm.get_devices_from_nsm(args.device, regions=args.region)
    if devices:
        devices_final = concurr_f(get_lag_br, sorted(devices), dev_type=args.search)
        if devices_final:
            device_output = list(filter(None.__ne__, devices_final))
            if device_output:
                found = [x[0] for x in device_output if x[1] == True and x[0]]
                not_found = [x[0] for x in device_output if x[1] == False and x[0]]
            if not_found:
                if DEVICE_INTER:
                    print()
                    print(
                        bcolors.OKGREEN
                        + "No Cabling issues found on the following {} and {} devices in {}:".format(
                            args.device, args.search, args.region or args.locator
                        )
                        + bcolors.ENDC
                    )
                    json_dict = {
                        x: sorted(
                            list(v), key=lambda x: int(x.split("-")[-1].split("r")[1])
                        )
                        for y in not_found
                        for x, v in y.items()
                    }
                    if json_dict:
                        jsonify(json_dict)
            if found:
                print()
                print(
                    bcolors.FAIL
                    + "[!][!] Cabling issues found on the following {} and {} devices in {}:".format(
                        args.device, args.search, args.region or args.locator
                    )
                    + bcolors.ENDC
                )
                jsonify(found)
            else:
                if not DEVICE_INTER:
                    print()
                    print(
                        bcolors.WARNING
                        + "[!] NO Connectivity information found between {} and {} devices in {}".format(
                            args.device, args.search, args.region or args.locator
                        )
                        + bcolors.ENDC
                    )
    else:
        print(
            bcolors.FAIL
            + "No {} devices could be found in {}".format(args.device, args.region)
            + bcolors.ENDC
        )


def main():
    args = parse_args()
    if args:
        rundown(args)
        print()
        if args:
            kickoff_func(args)

        if FAILED_DEVICES:
            print(
                bcolors.FAIL
                + "Devices below had issues (device : error show in key/value format):"
                + bcolors.ENDC
            )
            for d, err in FAILED_DEVICES.items():
                print(d, err)


if __name__ == "__main__":
    main()

