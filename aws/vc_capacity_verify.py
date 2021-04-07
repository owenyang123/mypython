#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

"""
VC-CAR <--> Border Scaling Verification Script
Version  Date         Author     Comments
1.00      2019-12-24   eastmab@    First version:

***** Retrieves list of VC-CAR's for specified region
***** Extracts and counts number of links connected to Border
***** Verify all VC-CAR's have been verified
***** Verify which VC-CAR's have less than command-line specifed capacity (1600Gb
      default)--> Border
***** Show customer-facing capacity
***** Show possible oversubscription ratio

***** To Be Completed ***
 -- add verification for MX240's
 -- add hardware recommendation output for devices that need additional linecards

"""

import argparse
import collections
import concurrent.futures
import csv
import datetime
import itertools
import json
import logging
import pathlib
import signal
import textwrap

from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.modules import nsm
from dxd_tools_dev.portdata import portfunction
from isd_tools_dev.modules import nsm as nsm_isd

# Enables quick termination of script if needed
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',

# Enables logging to be activated based on tags
logging.basicConfig(
    format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S", level=logging.INFO
)
logging.debug("Logging enabled")

AGG = []
CAS_INFO_NEEDED = []
FAIL_DEVICES = {}


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


REGIONS = [
    "iad",
    "pdx",
    "bjs",
    "fra",
    "bom",
    "hkg",
    "nrt",
    "cmh",
    "arn",
    "dub",
    "syd",
    "lhr",
    "pek",
    "yul",
    "kix",
    "corp",
    "cdg",
    "bah",
    "zhy",
    "sfo",
    "sin",
    "icn",
    "gru",
]


def intro_message(message, args):
    print(
        bcolors.HEADER
        + "###############################################################################"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###### Script to verify capacity between VC-CAR's <---> Border devices  #######"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###############################################################################"
        + bcolors.ENDC
    )
    print("")
    print(
        bcolors.BOLD
        + "Time script started: {}".format(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        + bcolors.ENDC
    )
    print("")
    args_check(args)
    print("")
    print(bcolors.WARNING + "Regions that will be checked:" + bcolors.ENDC)
    print("\n".join(str(v.upper()) for v in message))
    print("")


def parse_args() -> str:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
    Script verifies VC-CAR capacity towards border devices.
    -- Proper stripping should be at least 160Gb VC-CAR <---> Border devices
    Usage:
        * python vc_capacity_verify.py -r 'IAD' #Run script against VC-CAR's in IAD region
        * python vc_capacity_verify.py -r 'all' #Run script against VC-CAR's in all regions
        * python vc_capacity_verify.py -r 'pdx' -p 'hio50' #Run script against VC-CAR's in a
          region and specify POP(s)
        * python vc_capacity_verify.py -r 'pdx' -p 'den50,sea4' -c 360 #Run
          script against VC-CAR's in PDX region specifying den50,sea4 POP's that
          don't have at least 360Gb backhaul border capacity
    """
        ),
    )
    # p.add_argument(
    #    "-fp", "--fping", action="store_true", help="enables the fping function"
    # )
    p.add_argument(
        "-r",
        "--region",
        help="comma separated list of regions",
        type=str,
        nargs="?",
        default="pdx",
        required=True,
    )
    p.add_argument(
        "-p",
        "--pop",
        help="comma separated list of POP's",
        type=str,
        nargs="?",
        # default="pdx2, pdx4",
    )
    p.add_argument(
        "-c", "--capacity", help="Backhaul capacity threshold", type=int, default=1600,
    )
    p.add_argument(
        "-cs",
        "--csv",
        action="store_true",
        help="Enables cutsheet generation",
        # default=False,
    )
    return p.parse_args()


def show_links(e: dict, region: str):
    """
    Prints easily-readable lag information between VC devices and Border devices:
    gru1-vc-car-r2:
    10.0Gb --ae20--> gru1-br-tra-r1
    10.0Gb --ae21--> gru1-br-tra-r2
    Total Capacity: 20.0Gb

    gru3-vc-car-r1:
    10.0Gb --ae20--> gru3-br-tra-r1
    10.0Gb --ae21--> gru3-br-tra-r2
    Total Capacity: 20.0Gb
    """
    print()
    print(bcolors.UNDERLINE + "REGION: {}".format(region.upper()) + bcolors.ENDC)
    for v, vv in sorted(e.items()):
        print(bcolors.HEADER + "{}:".format(v) + bcolors.ENDC)
        for rr in sorted(vv[:-1]):
            print("{}Gb --{}--> {}".format(int(rr[0]) / 1000, rr[1], rr[2]))
        print(bcolors.WARNING + "Total Capacity: {}Gb".format(vv[-1]) + bcolors.ENDC)
        print()
    print()


def get_cas_info():
    """
    Determines if VC-CAR has any VC-CAS neighbors
    """

    def cas_info(e):
        neigh = nsm.get_device_interfaces_from_nsm(e)
        extract_neigh = set(
            [
                v
                for l in neigh
                for x, v in l.items()
                if "vc-cas" in v and "Neighbor" in x
            ]
        )
        return list(extract_neigh)

    cas_check = [cas_info(v) for v in CAS_INFO_NEEDED]
    # /* CAS_INFO_NEEDED list needs to be cleared if "ALL" regions are being checked */
    CAS_INFO_NEEDED.clear()
    merged = list(itertools.chain(*cas_check))
    # extract_cas = [get_lag_info(aa, cas_info=True) for aa in sorted(merged)]
    extract_cas = concurr_f(merged, args=True)
    if extract_cas:
        cas_extract = {xx: v for l in extract_cas for xx, v in l.items()}
        cas_capac = concurr_customer(cas_extract)
        # cas_capac = [
        #     customer_capacity(x, b=y[-1], create=True, agg=True)
        #     for x, y in sorted(cas_extract.items())
        # ]
        if cas_capac:
            return cas_capac
    else:
        return False


def csv_gen(info: list):
    """
    Create CSV with capacity/oversubscription results
    """
    home = str(pathlib.Path.home())
    info_pre = list(filter(None.__ne__, info))
    #/* Remove duplicates from info_pre list */
    info = set(info_pre)
    with open(
        "{}/{}.csv".format(home, "Capacity-Results"), "w", newline=""
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "Host",
                "Border Capacity",
                "Customer-facing Capacity",
                "Oversubscription Ratio",
            ]
        )
        for a in sorted(info, key=lambda xx: float(xx[3].split(":")[0]), reverse=True):
            writer.writerow([a[0], a[1], a[2], a[3]])
            #writer.writerow([a[0], a[1], a[2], "{}:1".format(a[3])])


def customer_capacity(e: str, b=None, agg=True, create=True):
    """
    Gathers customer-facing capacity and if "customer"
    isn't found in interface description then VC-CAS
    verification check is run further along in the script
    """
    if create:
        interfaces = nsm_isd.get_raw_device(e)
        customer_links = [
            xx
            for xx in interfaces["interfaces"]
            if "customer" in xx["interface_description"]
        ]
        customer_info = [
            (xx["bandwidth_mbit"], xx["short_name"]) for xx in customer_links
        ]
        cust_filt = [t for t in customer_info if not "ae" in t[1]]
        add_customer = [int(x[0]) for x in cust_filt]
        customer_total = sum(add_customer) / 1000
        if customer_total:
            if agg:
                return (
                    e,
                    "{}Gb".format(b),
                    "{}Gb".format(customer_total),
                    "{:.2f}:1".format(round(customer_total / b, 2)),
                )
        else:
            CAS_INFO_NEEDED.append(e)
    else:
        return False


def get_lag_info(sp: str, cas_info=False) -> dict:
    """
    Creates dictionary based on lag information pulled from NSM.
    cas_info tag will pull information from VC-CAS's otherwise
    information will be pulled from VC-CAR's
    Sums up total lag capacity between VC device(s) and border device(s)
    """
    try:
        device_agg = {}
        logging.debug(sp)
        interfaces = nsm_isd.get_raw_device(sp)
        # /* agg_links var needed to be modified for lax61 verification */
        pre_agg_links = [
            xx
            for xx in interfaces["interfaces"]
            if "aggregate" in xx["class"]  # or "physical" in xx["class"]
        ]
        agg_links = [x for x in pre_agg_links if "aggregation_members" in x]
        # /* End of new agg_links var */
        if agg_links:
            neigh = nsm.get_device_interfaces_from_nsm(sp)
            if cas_info:
                neigh_info = {
                    l["Name"]: l["Neighbor"] for l in neigh if "Neighbor" in l
                }
                if neigh_info:
                    device_info = [
                        (xx["bandwidth_mbit"], xx["short_name"], bb)
                        for xx in agg_links
                        for aa, bb in neigh_info.items()
                        if "vc-dar" in xx["interface_description"].lower()
                        or "vc-bar" in xx["interface_description"].lower()
                        or "vc-car" in xx["interface_description"].lower()
                        or "vc-cor" in xx["interface_description"].lower()
                        or "vc-edg" in xx["interface_description"].lower()
                        if aa
                        for yy in xx["aggregation_members"]
                        if aa == yy["name"]
                    ]
            else:
                neigh_info = {
                    l["Name"]: l["Neighbor"]
                    for l in neigh
                    if "Neighbor" in l
                    or "br-agg" in l
                    or "br-tra" in l
                    or "vc-bar" in l
                    or "vc-cor" in l
                    or "vc-dar" in l
                    or "vc-edg" in l
                }
                if neigh_info:
                    device_info = [
                        (xx["bandwidth_mbit"], xx["short_name"], bb)
                        for xx in agg_links
                        for aa, bb in neigh_info.items()
                        if "vc-dar" in xx["interface_description"].lower()
                        or "vc-bar" in xx["interface_description"].lower()
                        or "vc-cor" in xx["interface_description"].lower()
                        or "vc-edg" in xx["interface_description"].lower()
                        or "br-tra" in xx["interface_description"].lower()
                        or "br-agg" in xx["interface_description"].lower()
                        if aa
                        for yy in xx["aggregation_members"]
                        if aa == yy["name"]
                        # if "aggregation" in x
                    ]
            device_info = list(set(device_info))
        # /*New section regarding Capacity */
        add = [int(x[0]) for x in device_info]
        total = sum(add) / 1000

        if device_info:
            device_info.append(total)
            device_agg[sp] = device_info
            # /* End of new capacity section */
        else:
            FAIL_DEVICES[sp] = [("0", "NotFound", "NotFound"), 0]
        return device_agg

    except:
        pass


def verify_failure(devices: list) -> dict:
    """
    Attempts to resolve why device was
    pulled from NSM
    """
    output = [nsm_isd.get_raw_device(x) for x in devices]
    info = {xx["name"]: xx["polling_status"] for xx in output if isinstance(xx, dict)}
    diff = devices - info.keys()
    if diff:
        for m in diff:
            info[m] = "Unknown Reason"
    return info if info else None


def fmt_output(info):
    """
    Prints relevant device information in easily-readable format:
          Host                      Border Capacity   Customer-facing Capacity    Oversubscription Ratio
    gru1-vc-car-r2                      20.0Gb               365.0Gb                18.25
    gru1-vc-car-r1                      20.0Gb               371.0Gb                18.55
    gru3-vc-car-r1                      20.0Gb               107.0Gb                 5.35
    gru3-vc-car-r2                      20.0Gb               102.0Gb                  5.1
    gig51-vc-car-gru-r2                160.0Gb                 8.0Gb                 0.05
    gig51-vc-car-gru-r1                150.0Gb                 8.0Gb                 0.05
    """
    info = list(filter(None.__ne__, info))
    if info:
        print()
        print(
            bcolors.BOLD
            + "{: >10}  {: >35}  {: >25} {: >25}".format(
                "Host",
                "Border Capacity",
                "Customer-facing Capacity",
                "Oversubscription Ratio",
            )
            + bcolors.ENDC
        )
        for a in sorted(info, key=lambda xx: float(xx[3].split(":")[0]), reverse=True):
            if 7 <= float(a[3].split(".")[0]) <= 40:
                print(
                    bcolors.FAIL
                    + "{: <20}  {: >20}  {: >20} {: >20}".format(
                        a[0], a[1], a[2], a[3]
                    )
                    + bcolors.ENDC
                )
            elif 4 <= float(a[3].split(".")[0]) <= 7:
                print(
                    bcolors.WARNING
                    + "{: <20}  {: >20}  {: >20} {: >20}".format(
                        a[0], a[1], a[2], a[3]
                    )
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "{: <20}  {: >20}  {: >20} {: >20}".format(
                        a[0], a[1], a[2], a[3]
                    )
                    + bcolors.ENDC
                )
    else:
        print(
            bcolors.WARNING
            + "No info found. If VC-CAS verification enabled that may show customer facing capacity"
            + bcolors.ENDC
        )


def concurr_f(xx: list, args=False) -> list:
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        vc_car_final = {executor.submit(get_lag_info, x, cas_info=args): x for x in xx}
        for future in concurrent.futures.as_completed(vc_car_final):
            info = vc_car_final[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                logging.error(e)
                pass
    return f_result if f_result else None


def concurr_customer(xx: dict) -> list:
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        vc_car_final = {
            executor.submit(customer_capacity, x, b=y[-1], create=True): (x, y)
            for (x, y) in sorted(xx.items())
        }
        for future in concurrent.futures.as_completed(vc_car_final):
            info = vc_car_final[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                logging.error(e)
                pass
    return f_result if f_result else None


def args_check(x):
    print(bcolors.BOLD + "Command-line Args Enabled:" + bcolors.ENDC)
    if x.region:
        print(bcolors.WARNING + "Region Verification: [X]" + bcolors.ENDC)
    else:
        print(bcolors.WARNING + "Region Verification: [ ]" + bcolors.ENDC)
    if x.pop:
        print(bcolors.WARNING + "PoP Verification: [X]" + bcolors.ENDC)
    else:
        print(bcolors.WARNING + "PoP Verification: [ ]" + bcolors.ENDC)
    if x.capacity:
        print(bcolors.WARNING + "Capacity Verification: [X]" + bcolors.ENDC)
    else:
        print(bcolors.WARNING + "Capacity Verification: [ ]" + bcolors.ENDC)
    if x.csv:
        print(bcolors.WARNING + "CSV Generation: [X]" + bcolors.ENDC)
    else:
        print(bcolors.WARNING + "CSV Generation: [ ]" + bcolors.ENDC)


def region_verify(func_to_decorate):
    """
    Decorator function to determind if region exists or
    error would occur when trying to query NSM for information
    No need to waste API calls to resource
    """

    def new_func(original_args):
        logging.debug("Function has been decorated.  Congratulations.")
        logging.debug("original_args: {}".format(original_args))
        if "all" in original_args.region or "ALL" in original_args.region:
            intro_message(["ALL"], original_args)
            return [func_to_decorate(r, original_args) for r in REGIONS]
        else:
            region_to_exec = [
                l
                for l in REGIONS
                for x in original_args.region.split()
                if l in x.lower()
            ]
            if region_to_exec:
                intro_message(region_to_exec, original_args)
                return [
                    func_to_decorate(original_args.region, original_args)
                    for r in region_to_exec
                ]
            else:
                print(
                    bcolors.FAIL
                    + "{a} not found, please verify if {a} is a DX region(s) ".format(
                        a=original_args.region.upper()
                    )
                    + bcolors.ENDC
                )

    return new_func


@region_verify
def kickoff_func(region, args):
    """
    Main function that retrieves information and orders
    the way functions are ran
    """
    capacity = args.capacity
    print(
        bcolors.UNDERLINE
        + "###### Verifying VC-CAR/CAS <--> Border striping in {} ######....".format(
            region.upper()
        )
        + bcolors.ENDC
    )
    vc_cars = nsm.get_devices_from_nsm("vc-car", regions=region)
    #if args.csv:
    #    agg = []
    if args.pop:
        print(bcolors.HIGHGREEN + "POP VERIFICATION ENABLED" + bcolors.ENDC)
        print(
            bcolors.HEADER
            + "THESE POP's WILL BE CHECKED: {}".format("".join(args.pop))
            + bcolors.ENDC
        )
        vc_cars = [
            xx for xx in vc_cars for a in args.pop.split(",") if xx.startswith(a)
        ]
        logging.debug(vc_cars)
    if vc_cars:
        vc_car_final = concurr_f(vc_cars, args=False)
        vc_car_final = list(filter(None.__ne__, vc_car_final))
        print(
            bcolors.HEADER
            + "######## Region: {} ########".format(region.upper())
            + bcolors.ENDC
        )
        if vc_car_final:
            x = sorted(vc_car_final, key=lambda d: list(d.values()))
            if x:
                extract = sorted([xx for l in x for xx, v in l.items()])
                print(
                    bcolors.WARNING
                    + "Verifying all devices in {} were checked..".format(
                        region.upper()
                    )
                    + bcolors.ENDC
                )
                if len(vc_cars) == len(extract):
                    print(
                        bcolors.OKGREEN
                        + "All devices in {} are accounted for: {} out of {} verified".format(
                            region.upper(), len(extract), len(vc_cars)
                        )
                        + bcolors.ENDC
                    )
                else:
                    final = list(set(extract).symmetric_difference(vc_cars))
                    if final:
                        print(
                            bcolors.FAIL
                            + "One or more devicesin {} will not be verified.. looking for issues now ".format(
                                region.upper()
                            )
                            + bcolors.ENDC
                        )
                        logging.debug(final)
                        failed_devices = verify_failure(final)
                        print("\n".join(str(v) for v in failed_devices.items()))
                print()
                print(
                    bcolors.WARNING
                    + "Checking which devices have less than {}Gb capacity backhaul with Border devices".format(
                        capacity
                    )
                    + bcolors.ENDC
                )
                # /* New extract dict comp based on args.capacity flag */
                extract = {
                    xx: v for l in x for xx, v in l.items() if v[-1] < args.capacity
                }
                if extract:
                    print(
                        bcolors.FAIL
                        + "{} ({:.0%}) devices have less than {}Gb capacity to Border Devices".format(
                            len(extract), len(extract) / len(vc_cars), args.capacity
                        )
                        + bcolors.ENDC
                    )
                    # /* Show specific LAG information per device */
                    show_links(extract, region)
                    print(
                        bcolors.BOLD
                        + "Obtaining Customer/Border Capacity Information.."
                        + bcolors.ENDC
                    )
                    ov_ratio = concurr_customer(extract)
                    # ov_ratio = [
                    #     customer_capacity(x, b=y[-1], create=True)
                    #     for x, y in sorted(extract.items())
                    # ]
                    if ov_ratio:
                        fmt_output(ov_ratio)
                        if args.csv:
                            AGG.extend(ov_ratio)
                        print()
                    if CAS_INFO_NEEDED:
                        print(
                            bcolors.WARNING
                            + "## VC-CAS Information below: ##"
                            + bcolors.ENDC
                        )
                        print(
                            bcolors.HIGHGREEN
                            + "VC-CAS Verification Enabled"
                            + bcolors.ENDC
                        )
                        cas_final = get_cas_info()
                        print()
                        if cas_final:
                            fmt_output(cas_final)
                            if args.csv:
                                AGG.extend(cas_final)
                            print()
                        else:
                            print(
                                bcolors.WARNING
                                + "No VC-CAS information found for devices below.."
                                + bcolors.ENDC
                            )
                            print("\n".join(str(x) for x in CAS_INFO_NEEDED))
                else:
                    print(
                        bcolors.OKGREEN
                        + "All devices appear to have at least {}Gb backhaul capacity".format(
                            capacity
                        )
                        + bcolors.ENDC
                    )
        else:
            print(
                "No VC-CAR <--> Border information found in  {} region".format(
                    region.upper()
                )
            )
    else:
        print(
            bcolors.FAIL
            + "No VC-CAR devices found in {} region".format(region.upper())
            + bcolors.ENDC
        )
    #if agg:
    #    print(bcolors.HIGHGREEN + "CSV Generation Enabled" + bcolors.ENDC)
    #    csv_gen(agg)
    #    # print(ov_ratio)
    #    # print(cas_final)
    if FAIL_DEVICES:
        print()
        print(
            bcolors.FAIL + "These devices failed verification test(s):" + bcolors.ENDC
        )
        print("\n".join(str(v for v in FAIL_DEVICES.items())))


def main():
    args = parse_args()
    now_time = datetime.datetime.now()
    if args:
        placeholder = kickoff_func(args)
        if args.csv:
            print(bcolors.HIGHGREEN + "CSV Generation Enabled" + bcolors.ENDC)
            csv_gen(AGG)
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

