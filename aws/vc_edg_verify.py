#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

"""
Backhaul <--> VC-EDG <--> BF Capacity Verification Script
(BF = Blackfoot devices)
Version  Date         Author     Comments
1.00      2019-012-06   eastmab@    First version:
2.00      2020-001-08   eastmab@    Second version:

Program verifies capacity differential between BR-AGG/VC-BAR/VC-FAB <--> VC-EDG
and then from VC-EDG to BF devices

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


FAILED_DEVICE = {}
BF_DEVICES = collections.defaultdict(list)
BF_NARROW = collections.defaultdict(list)


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


def intro_message(message):
    print(
        bcolors.HEADER
        + "#################################################################################################"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "######## Script to verify capacity differential between VC-EDG's and Backhaul/BF devices  #######"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "#################################################################################################"
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
    print(bcolors.WARNING + "Regions that will be checked:" + bcolors.ENDC)
    print("\n".join(str(v.upper()) for v in message))
    print("")


def parse_args() -> str:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
    Script verifies VC-EDG (MX's) scaling with BF devices.
    -- Proper stripping should be 16 10Gb VC-EDG <---> BF devices
    Usage:
        * python vc_edg_verify.py -r 'IAD' #Run script against VC-EDG's in IAD region
        * python vc_edg_verify.py -r 'all' #Run script against VC-EDG's in all regions
        * python vc_edg_verify.py -r 'pdx', -a 'pdx2,pdx4' #Run script against VC-EDG's in a
          region and specify AZ(s)
        * python vc_edg_verify.py -r 'iad' -a 'iad7' --cutsheet #Generate cutsheet for AZ devices
    """
        ),
    )
    p.add_argument(
        "-c",
        "--cutsheet",
        action="store_true",
        help="Enables cutsheet generation",
        # default=False,
    )
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
        "-a",
        "--az",
        help="comma separated list of AZ's",
        type=str,
        nargs="?",
        # default="pdx2, pdx4",
    )
    return p.parse_args()


class CustomExceptionName(Exception):
    """Still an exception raised when uncommon things happen"""
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message) # 


class Device:
    def __init__(self, name, capacity=160):
        self.name = name
        self.capacity = int(capacity)
        self.interfaces = nsm_isd.get_raw_device(name)
        self.agg_links = [
            xx for xx in self.interfaces["interfaces"] if "physical" in xx["class"]
        ]
        self.vc_info = []
        self.vc_agg_info = collections.defaultdict(int)
        self.vc_neighbors = []
        self.bf_info = []
        self.bf_agg_info = collections.defaultdict(int)
        self.bf_neighbors = []
        self.vc_cap = 0
        self.bf_cap = 0
        self.bw_diff = 0

    def get_agg_info(self):
        if len(self.agg_links) > 1:
            device_info = [
                (
                    x["neighbors"]["link_layer"]["device_name"],
                    x["aggregation"]["name"],
                    x["bandwidth_mbit"],
                )
                for x in self.agg_links
                if "es-svc-x" in x["interface_description"].lower()
                or "es-svc-v" in x["interface_description"].lower()
                or "es-svc-p" in x["interface_description"].lower()
                or "es-svc-c" in x["interface_description"].lower()
                or "es-svc-r" in x["interface_description"].lower()
                or "vc-bar" in x["interface_description"].lower()
                or "vc-fab" in x["interface_description"].lower()
                or "br-agg" in x["interface_description"].lower()
                if "aggregation" in x and not "down" in x["status"]
                if "neighbors" in x and "xe-" in x["name"]  # To exclude Vegemite racks
            ]
            if device_info:
                self.vc_info = [
                    x
                    for x in device_info
                    for y in x
                    if "-vc-fab" in y or "-vc-bar" in y or "br-agg" in y
                ]
                self.bf_info = [x for x in device_info for y in x if "es-svc" in y]
                return (
                    self.name,
                    device_info,
                    self.vc_info,
                    self.bf_info,
                )

    def get_bf_info(self):
        if self.bf_info:
            for l in self.bf_info:
                self.bf_agg_info[l[0]] += int(l[2]) / 1000
            self.bf_neighbors = [x[0] for x in self.bf_info]
            if self.bf_neighbors:
                BF_DEVICES[self.name.split("-")[0]].extend(self.bf_neighbors)
                BF_NARROW[self.name].extend(self.bf_neighbors)
            add_bf = [int(x[2]) for x in self.bf_info]
            self.bf_cap = sum(add_bf) / 1000
            return self.bf_neighbors, self.bf_cap

    def get_vc_info(self):
        if self.vc_info:
            # /*New section regarding Capacity */
            # /* VC-FAB's need to be excluded if VC-BAR's are also in list of neighbors */
            _temp_vc_neighbors = self.mod_vc_info(self.vc_info)
            for l in _temp_vc_neighbors:
                self.vc_agg_info[l[0]] += int(l[2]) / 1000
            self.vc_neighbors = [x[0] for x in _temp_vc_neighbors]
            add_vc = [int(x[2]) for x in _temp_vc_neighbors]
            self.vc_cap = sum(add_vc) / 1000
            return self.vc_neighbors, self.vc_cap

    def mod_vc_info(self, x):
        place = []
        for p in x:
            if "vc-bar" or "vc-fab" in all(v[0] for v in p):
                if "vc-bar" in p[0]:
                    place.append(p)
                elif not "vc-fab" in p[0]:
                    place.append(p)
        return place if place else x

    def get_capacity_info(self):
        if self.vc_cap > 1 and self.bf_cap > 1:
            if self.bf_cap > self.vc_cap:
                self.bw_diff = self.bf_cap - self.vc_cap
            elif self.vc_cap > self.bf_cap:
                self.bw_diff = self.vc_cap - self.bf_cap


def concurr_f(xx: list) -> list:
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        vc_edg_final = {executor.submit(get_lag_info, x): x for x in xx}
        for future in concurrent.futures.as_completed(vc_edg_final):
            info = vc_edg_final[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                pass
    return f_result if f_result else None


def get_lag_info(sp: str, capacity=160) -> dict:
    device_info = []
    try:
        out = Device(sp, capacity)
        if out:
            methods_to_run = [
                out.get_agg_info(),
                out.get_bf_info(),
                out.get_vc_info(),
                out.get_capacity_info(),
            ]
        if out.vc_cap > 1 and out.bf_cap > 1:
            device_info.append((out.name, out.vc_cap, out.bf_cap, out.bw_diff))
        if device_info:
            return device_info

    except Exception as e:
        FAILED_DEVICE[sp] = e
        pass


def audit_device(func_to_decorate):
    def new_func(devices: dict, *a, **k):
        audit = {}
        for x, cc in devices.items():
            count = portfunction.get_device_available_port(x)
            ucount = {int(r) * len(v) / 1000: len(v) for r, v in count.items()}
            if ucount:
                logging.debug(ucount)
                for c, xx in ucount.items():
                    if xx + cc >= 16:
                        audit[
                            x
                        ] = "{} Ports Needed | {} Ports Available | {} Gb capacity available".format(
                            cc, xx, c
                        )
                    else:
                        audit[
                            x
                        ] = "{} Ports Needed | {} Ports Available | {} Gb capacity available | LINECARD-ADDITION-NEEDED".format(
                            cc, xx, c
                        )
            else:
                audit[x] = "NSM Portfunction could not find any available ports"

        if audit:
            return [
                #func_to_decorate(audit, *a, **k)
                func_to_decorate(r, v, *a, **k)
                for r, v in sorted(audit.items())# if not "LINECARD-ADDITION-NEEDED" in r
            ]

    return new_func


# /* Decorator Testing function */
# @audit_device
# def test_func(r, cutsheet=False):
#    if cutsheet:
#        print("DECORATOR IS WORKING!!!")
#        print(r)
#    else:
#        print("ARGS ISN'T WORKING")


def get_bf_neigh(test: str):
    try:
        diff = set(BF_NARROW[test]) ^ set(BF_DEVICES[test.split('-')[0]])
        diff_u = [l for l in diff for x in set(BF_NARROW[test]) if len(l) == len(x)]
        return list(set(diff_u))
        #return list(set(BF_NARROW[test]) ^ set(BF_DEVICES[test.split('-')[0]]))
    except CustomExceptionName as error:
        print(str(error)) # Very bad mistake
        print("Detail: {}".format(error.payload))


@audit_device
def cutsheet_gen(d: str, v, cutsheet=False):
    """
    vc = {'nrt12-vc-edg-r1': '8 Current Ports | 8 Ports Available | 80.0 Gb capacity available', 'nrt20-vc-edg-r2': '8 Current Ports | 9 Ports Available | 90.0 Gb capacity available', 'nrt20-vc-edg-r1': '8 Current Ports | 9 Ports Available | 90.0 Gb capacity available', 'nrt7-vc-edg-r2': '8 Current Ports | 42 Ports Available | 420.0 Gb capacity available', 'nrt7-vc-edg-r1': '8 Current Ports | 41 Ports Available | 410.0 Gb capacity available'}
    for d, i in vc.items():
        count = portfunction.get_device_available_port(d)
        info = {d : l[:i] for a, l in count.items() if a == '10000'}
    /* Linux command to find .csv files created after/before 60 minutes:
        - find . -maxdepth 1 -iname '*.csv' -mmin +60 #After 60 minutes
        - find . -maxdepth 1 -iname '*.csv' -mmin -60 #within 60 minutes
    """
    oppo_vc_edgs = get_bf_neigh(d)
    clean_neigh = [x for x in oppo_vc_edgs if any(i in x.split('-')[-1][1] for i in ['1', '2', '3'])]
    logging.debug(clean_neigh)
    if cutsheet and not "LINECARD-ADDITION-NEEDED" in v or "could not find any available ports" in v:
        print(d, v)
        a_optic = "SFP+-10G-LR"
        home = str(pathlib.Path.home())
        count = portfunction.get_device_available_port(d)
        info = {d: l for a, l in count.items() if a == "10000"}
        with open("{}/{}.csv".format(home, d), "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                ["a_hostname", "a_interface", "a_optic", "z_hostname", "z_interface"]
            )
            for a, b in info.items():
                for bb in sorted(b):
                    for cc in sorted(clean_neigh):
                        writer.writerow([a, bb, a_optic, cc, "TEST"])
                        #writer.writerow([a, bb, a_optic, "ES-SVC-V", "TEST"])

    else:
        print(d, v)


def fmt_output(info: list):
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
                "Backhaul Capacity",
                "Blackfoot Capacity",
                "Capacity Differential",
            )
            + bcolors.ENDC
        )
        for a in sorted(info, key=lambda xx: float(xx[3]), reverse=True):
            if 71 <= float(a[3]) <= 1000:
                print(
                    bcolors.FAIL
                    + "{: <20}  {: >20}Gb  {: >20}Gb {: >20}".format(
                        a[0], a[1], a[2], a[3]
                    )
                    + bcolors.ENDC
                )
            elif 40 <= float(a[3]) <= 70:
                print(
                    bcolors.WARNING
                    + "{: <20}  {: >20}Gb  {: >20}Gb {: >20}".format(
                        a[0], a[1], a[2], a[3]
                    )
                    + bcolors.ENDC
                )
            else:
                print(
                    bcolors.OKGREEN
                    + "{: <20}  {: >20}Gb  {: >20}Gb {: >20}".format(
                        a[0], a[1], a[2], a[3]
                    )
                    + bcolors.ENDC
                )
    else:
        print(bcolors.WARNING + "No info found" + bcolors.ENDC)


def region_verify(func_to_decorate: str):
    def new_func(original_args):
        logging.debug("Function has been decorated.  Congratulations.")
        logging.debug("original_args: {}".format(original_args))
        if "all" in original_args.region or "ALL" in original_args.region:
            intro_message(["ALL"])
            return [func_to_decorate(r, original_args) for r in REGIONS]
        else:
            region_to_exec = [
                l
                for l in REGIONS
                for x in original_args.region.split()
                if l in x.lower()
            ]
            if region_to_exec:
                intro_message(region_to_exec)
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


def get_port_info(temp: tuple) -> dict:
    audit = {}
    for y in temp:
        if 160 <= y[1] and 160 >= y[2]:
            audit[y[0]] = 16 - int(y[2] / 10)
        elif 160 >= y[1] and 160 <= y[2]:
            audit[y[0]] = 16 - int(y[1] / 10)
        elif 160 >= y[1] and 160 >= y[2]:
            audit[y[0]] = 32 - (int(y[1] / 10) + int(y[2] / 10))
    if audit:
        # /* Remove '0' values from dict */
        audit = {k: v for k, v in audit.items() if v >= 1}
        return audit if audit else None


@region_verify
def kickoff_func(region: str, args):
    print()
    print(
        bcolors.UNDERLINE
        + "###### Verifying VC-EDG Backhaul/Blackfoot capacity in {} ######....".format(
            region.upper()
        )
        + bcolors.ENDC
    )
    # /* Extract all vc-edg devices in region from NSM
    vc_edgs = nsm.get_devices_from_nsm("vc-edg", regions=region)
    # /* If AZ args specified then extract devices from specified AZ(s)
    if args.az:
        print(bcolors.HIGHGREEN + "AZ VERIFICATION ENABLED" + bcolors.ENDC)
        print(
            bcolors.HEADER
            + "THESE AZs WILL BE CHECKED: {}".format("".join(args.az))
            + bcolors.ENDC
        )
        vc_edgs = [xx for xx in vc_edgs for a in args.az.split(",") if xx.startswith(a)]
        logging.debug(vc_edgs)
    if vc_edgs:
        vc_edg_final = concurr_f(vc_edgs)
        vc_edg_final = list(filter(None.__ne__, vc_edg_final))
        if vc_edg_final:
            c_devices = list(itertools.chain(*vc_edg_final))
            if c_devices:
                fmt_output(c_devices)
                print()
                audit_dict = get_port_info(c_devices)
                if audit_dict:
                    if args.cutsheet:
                        print(bcolors.HIGHGREEN + "Cutsheet generation is enabled"  + bcolors.ENDC)
                        print(bcolors.WARNING + "These VC-EDG <--> Blackfoot cutsheets will need to be modified according to your situation" + bcolors.ENDC)
                        print()
                    print(bcolors.BOLD + "VC-EDG Port Information:" + bcolors.ENDC)
                    cutsheet_gen(audit_dict, cutsheet=args.cutsheet)


def main():
    args = parse_args()
    now_time = datetime.datetime.now()
    if args:
        placeholder = kickoff_func(args)
    if FAILED_DEVICE:
        print()
        print(
            bcolors.FAIL
            + "[ALERT!] # of devices that failed verification: {}".format(
                len(FAILED_DEVICE)
            )
            + bcolors.ENDC
        )
        print("\n".join(str(v) for v in FAILED_DEVICE.items()))
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
