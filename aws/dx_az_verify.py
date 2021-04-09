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
import functools
import itertools
import json
import logging
import pathlib
import platform
import pprint
import re
import signal
import textwrap

from pygments import formatters, highlight, lexers

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


BR_AGGS = collections.defaultdict(list)
CACHE_CHECK = {}
FAILED_DEVICE = {}

tree = lambda: collections.defaultdict(tree)
root = tree()

# / * Will be enabled at later date */
# BF_DEVICES = collections.defaultdict(list)
# BF_NARROW = collections.defaultdict(list)


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
    "mxp",
]


BR_AGG_CHECK = False


# /* System verification check.. BR-AGG port availability check can only run on config-builder systems */
print()
print(
    bcolors.BOLD + "[!][!] Border Port Availability debug information:" + bcolors.ENDC
)
if "network-config-builder" in platform.node():
    BR_AGG_CHECK = True
    print(
        bcolors.OKGREEN
        + "BR-AGG port availability check can be performed on {}".format(
            platform.node()
        )
        + bcolors.ENDC
    )
    print(
        bcolors.OKGREEN
        + "Importing modules for Border Port Data information.."
        + bcolors.ENDC
    )
    from dxd_tools_dev.portdata import border as portdata
else:
    print(
        bcolors.WARNING
        + "Cannot run BR-AGG port availability check on {}".format(platform.node())
        + bcolors.ENDC
    )
print()


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
        self.payload = payload  # you could add more args

    def __str__(self):
        return str(self.message)  #


class Device:
    def __init__(self, name, capacity=160):
        self.name = name
        self.capacity = int(capacity)
        self.interfaces = nsm_isd.get_raw_device(name)
        self.agg_links = [
            xx for xx in self.interfaces["interfaces"] if "physical" in xx["class"]
        ]
        self.vc_bar = False
        self.vc_fab = False
        self.br_agg = False

        self.vc_bar_info = []
        self.vc_fab_info = []
        self.br_agg_info = []

        self.vc_bar_from_fab = {}
        self.vc_bar_from_border = {}

        self.vc_bar_agg_info = collections.defaultdict(int)
        self.vc_fab_agg_info = collections.defaultdict(int)
        self.br_agg_agg_info = collections.defaultdict(int)

        self.vc_bar_neighbors = []
        self.vc_fab_neighbors = []
        self.br_agg_neighbors = []

        self.bf_info = []
        self.bf_agg_info = collections.defaultdict(int)
        self.bf_neighbors = []

        self.cap_device_info = []
        self.design_type = ""

        self.vc_fab_cap = 0
        self.vc_bar_cap = 0
        self.br_agg_cap = 0
        self.bf_cap = 0

        self.bw_diff = 0

        self.pre_hmb = {}
        self.hmbv1 = {}
        self.hmbv2 = {}

        self.border_output = []

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
                # or "vc-agg" in x["interface_description"].lower()
                or "vc-bar" in x["interface_description"].lower()
                or "vc-fab" in x["interface_description"].lower()
                or "br-agg" in x["interface_description"].lower()
                if "aggregation" in x and not "down" in x["status"]
                if "neighbors" in x and "xe-" in x["name"]  # To exclude Vegemite racks
            ]
            if device_info:
                self.vc_bar_info = [
                    x
                    for x in device_info
                    for y in x
                    if "-vc-bar" in y
                    # or "vc-agg" in y
                ]
                self.vc_fab_info = [
                    x
                    for x in device_info
                    for y in x
                    if "-vc-fab" in y
                    # or "vc-agg" in y
                ]
                self.br_agg_info = [
                    x
                    for x in device_info
                    for y in x
                    if "br-agg" in y
                    # or "vc-agg" in y
                ]
                if len(self.vc_bar_info) > 1:
                    self.vc_bar = True
                if len(self.vc_fab_info) > 1:
                    self.vc_fab = True
                if len(self.br_agg_info) > 1:
                    self.br_agg = True

                self.bf_info = [x for x in device_info for y in x if "es-svc" in y]
                return (
                    self.name,
                    device_info,
                    self.vc_bar_info,
                    self.vc_fab_info,
                    self.br_agg_info,
                    self.bf_info,
                )

    def get_bf_info(self):
        if self.bf_info:
            for l in self.bf_info:
                self.bf_agg_info[l[0]] += int(l[2]) / 1000
            self.bf_neighbors = [x[0] for x in self.bf_info]
            # /* will be enabled at later date - Blackfoot checks are upcoming */
            # if self.bf_neighbors:
            # BF_DEVICES[self.name.split("-")[0]].extend(self.bf_neighbors)
            # BF_NARROW[self.name].extend(self.bf_neighbors)
            add_bf = [int(x[2]) for x in self.bf_info]
            self.bf_cap = sum(add_bf) / 1000
            return self.bf_neighbors, self.bf_cap

    def get_vc_info(self):
        if self.vc_bar:
            for l in self.vc_bar_info:
                self.vc_bar_agg_info[l[0]] += int(l[2]) / 1000
            self.vc_bar_neighbors = [x[0] for x in self.vc_bar_info]
            add_vc = [int(x[2]) for x in self.vc_bar_info]
            self.vc_bar_cap = sum(add_vc) / 1000
            return self.vc_bar_neighbors, self.vc_bar_cap
        if self.vc_fab:
            for l in self.vc_fab_info:
                self.vc_fab_agg_info[l[0]] += int(l[2]) / 1000
            self.vc_fab_neighbors = [x[0] for x in self.vc_fab_info]

            add_vc = [int(x[2]) for x in self.vc_fab_info]
            self.vc_fab_cap = sum(add_vc) / 1000
            return self.vc_fab_neighbors, self.vc_fab_cap
        if self.br_agg:
            for l in self.br_agg_info:
                self.br_agg_agg_info[l[0]] += int(l[2]) / 1000
            self.br_agg_neighbors = [x[0] for x in self.br_agg_info]
            add_vc = [int(x[2]) for x in self.br_agg_info]
            self.br_agg_cap = sum(add_vc) / 1000
            return self.br_agg_neighbors, self.br_agg_cap, dict(self.br_agg_agg_info)

    def hmb_check(self):
        if self.vc_bar and self.vc_fab or self.br_agg and self.vc_bar:
            self.design_type = (
                bcolors.WARNING
                + "Site is possibly in Hambone migration project"
                + bcolors.ENDC
            )
            # self.pre_hmb[self.name] = (
            self.hmbv2[self.name] = (
                self.get_cap_links(self.vc_bar_info),
                self.vc_bar_cap,
            )
            if self.vc_bar_neighbors:
                extract_vc_bars = set(self.vc_bar_neighbors)
                self.border_output = self.get_border_cap(extract_vc_bars)
        if self.br_agg and not self.vc_fab:
            self.design_type = bcolors.FAIL + "Pre-Hambone Design Found" + bcolors.ENDC
            self.pre_hmb[self.name] = (set(self.br_agg_neighbors), self.br_agg_cap)
        if self.vc_fab and not self.vc_bar:
            self.design_type = bcolors.OKBLUE + "HamboneV1 Design Found" + bcolors.ENDC
            self.hmbv1[self.name] = (
                self.get_cap_links(self.vc_fab_info),
                self.vc_fab_cap,
            )
            logging.debug(
                "Info is now needed for VC-BAR's that may be connected to VC-FAB's"
            )
            self.vc_bar_from_fab = self.get_fab_neigh(set(self.vc_fab_neighbors))
            if self.vc_bar_info:
                extract_vc_bars = set(self.vc_bar_info)
                self.border_output = self.get_border_cap(extract_vc_bars)
        if self.vc_bar and not self.vc_fab:
            self.design_type = bcolors.OKGREEN + "HamboneV2 Design Found" + bcolors.ENDC
            self.hmbv2[self.name] = (
                self.get_cap_links(self.vc_bar_info),
                self.vc_bar_cap,
            )
            if self.vc_bar_neighbors:
                extract_vc_bars = set(self.vc_bar_neighbors)
                self.border_output = self.get_border_cap(extract_vc_bars)

    def get_fab_neigh(self, devices):
        fab_to_bar_output = collections.defaultdict(list)
        extracted_vc_bars = []
        for name in devices:
            interfaces = nsm_isd.get_raw_device(name)
            fab_agg_links = [
                xx for xx in interfaces["interfaces"] if "physical" in xx["class"]
            ]
            device_info = [
                (
                    x["neighbors"]["link_layer"]["device_name"],
                    # x["aggregation"]["name"],
                    x["bandwidth_mbit"],
                )
                for x in fab_agg_links
                if "vc-bar" in x["interface_description"].lower()
                if "aggregation" in x and not "down" in x["status"]
                if "neighbors" in x and "xe-" in x["name"]  # To exclude Vegemite racks
            ]
            if device_info:
                hold_dict = collections.defaultdict(int)
                # fab_to_bar_output[name].append(device_info)
                for x in device_info:
                    if "vc-bar" in x[0]:
                        extracted_vc_bars.append(x[0])
                    hold_dict[x[0]] += int(x[1]) / 1000
                fab_to_bar_output[name].append(dict(hold_dict))
        if extracted_vc_bars:
            self.vc_bar_info = extracted_vc_bars
        if fab_to_bar_output:
            return dict(fab_to_bar_output)

    def get_cap_links(self, band_info):
        new_info = {}
        band = collections.Counter(band_info)
        for x, y in band.items():
            total = int(x[2]) * int(y)
            new_info[x[0]] = "{}Gb".format(total / 1000)

        return new_info

    def get_border_cap(self, vc_dev):
        border_agg_info = collections.defaultdict(list)
        for sp in vc_dev:
            logging.debug("GET_BORDER_CAP METHOD IS RUNNING")
            logging.debug(sp)
            try:
                if sp:  # not in CACHE_CHECK:
                    # /* Cache check will be enabled at later date - not worth perf optimization now */
                    # CACHE_CHECK[sp] = {}
                    out_br = BR_Device(sp)
                    if out_br:
                        methods_to_run = [
                            out_br.get_agg_info(),
                            out_br.get_br_info(),
                            out_br.get_percent(),
                            # out.get_capacity_info(),
                        ]
                    # CACHE_CHECK[sp] = {}
                    # if out_br.br_cap:
                    #    CACHE_CHECK[sp]["{}".format(out_br.br_cap)] = dict(
                    #        out_br.br_agg_info
                    #    )
                    if out_br.br_cap > 1:
                        # self.cap_device_info.append(
                        #    (out_br.name, out_br.br_cap, dict(out_br.br_agg_info),)
                        # )
                        border_agg_info[self.name].append(
                            (out_br.name, out_br.br_cap, dict(out_br.br_agg_info),)
                        )
                if border_agg_info:
                    self.vc_bar_from_border = border_agg_info
            except Exception as e:
                FAILED_DEVICE[vc_dev] = e
                pass

    def escape_ansi(self, line):
        ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", line)

    def get_bfoot_info(self, device=None, bf_info=None, bfoot_cap=None, success=False):
        def bfoot_hardware_check():
            print("BFOOT HARDWARE CHECK NEEDED")

        print(bcolors.BOLD + "Blackfoot Capacity/Striping Info:" + bcolors.ENDC)
        if success:
            hardware_check = False
            current_ports = 0
            requested = 16
            # print(bcolors.BOLD + "Blackfoot Capacity/Striping Info:" + bcolors.ENDC)
            print(
                bcolors.WARNING
                + "1. Verifying VC-EDG <--> Blackfoot Capacity"
                + bcolors.ENDC
            )
            # /* Temporary bandwidth calc code */
            bf_agg = collections.defaultdict(int)
            for l in bf_info:
                bf_agg[l[0]] += int(l[2]) / 1000
            if bf_agg:
                if 16 > len(dict(bf_agg)):
                    hardware_check = True
                    current_ports = 16 - len(dict(bf_agg))
                # for v, b in dict(bf_agg).items():
                print(
                    bcolors.BOLD
                    + "  1A. Blackfoot neighbors/striping below:"
                    + bcolors.ENDC
                )
                for v, b in sorted(dict(bf_agg).items()):
                    print("      {}: {}Gb".format(v, float(b)))
                print("   Total Capacity: {}Gb".format(bfoot_cap))
            print()
            root[self.name.split("-")[0]][self.name][
                "{}".format(self.escape_ansi(self.design_type))
            ]["VC-EDG to Blackfoot Capacity (Gb's)"] = bfoot_cap
            if hardware_check:
                root[self.name.split("-")[0]][self.name][
                    "{}".format(self.escape_ansi(self.design_type))
                ][
                    "Blackfoot Striping (Min: 16 Blackfoot's)"
                ] = "Fail ({} Blackfoot's found)".format(
                    len(dict(bf_agg))
                )
                print(
                    bcolors.BOLD
                    + "  1B. Less than 16 BFoot devices found, will check {} for availabe ports for striping purposes".format(
                        device.upper()
                    )
                    + bcolors.ENDC
                )
                print(
                    bcolors.WARNING
                    + "      Ports needed: {}".format(current_ports)
                    + bcolors.ENDC
                )
                self.audit_port_avail(
                    self.name, current_ports=current_ports, requested=16, check="BFoot"
                )
                # count = portfunction.get_device_available_port(device)
                # ucount = {int(r) * len(v) / 1000: len(v) for r, v in count.items()}
                # if ucount:
                #     logging.debug(ucount)
                #     for c, xx in ucount.items():
                #         if xx + current_ports >= requested:
                #             print(
                #                 "        {}: {} Ports Needed | {} Ports Available | {} Gb capacity available".format(
                #                     device, current_ports, xx, c
                #                 )
                #             )
                #         else:
                #             print(
                #                 "        {}: {} Ports Needed | {} Ports Available | {} Gb capacity available | LINECARD-ADDITION-NEEDED".format(
                #                     device, current_ports, xx, c
                #                 )
                #             )
                #             verify_hardware = self.corr_info(device)
                #             if verify_hardware:
                #                 logging.debug(verify_hardware)
                #                 self.hardware_info(verify_hardware)
                #         print()
                # else:
                #     print("        NSM Portfunction could not find any available ports")
            else:
                root[self.name.split("-")[0]][self.name][
                    "{}".format(self.escape_ansi(self.design_type))
                ][
                    "Blackfoot Striping (Min: 16 Blackfoot's)"
                ] = "Success  ({} Blackfoot's found)".format(
                    len(dict(bf_agg))
                )
                print(
                    bcolors.OKGREEN
                    + "   Blackfoot striping is adequate for {}".format(device.upper())
                    + bcolors.ENDC
                )
                print()
        else:
            print(
                bcolors.FAIL
                + "   [!WARNING] No Blackfoot devices found [!]"
                + bcolors.ENDC
            )
            print()
            root[self.name.split("-")[0]][self.name][
                "{}".format(self.escape_ansi(self.design_type))
            ]["Blackfoot Striping (Min: 16 Blackfoot's)"] = "No Blackfoot devices found"

    def corr_info(self, devices: list) -> dict:
        output = {}
        table = ddb.get_ddb_table("dx_devices_table")
        # p = {x: ddb.get_device_from_table(table, "Name", x)["Hardware"] for x in devices}
        p = {devices: ddb.get_device_from_table(table, "Name", devices)["Hardware"]}
        logging.debug(p)
        for r, v in p.items():
            if "SCB" in v:
                output["{} : {}".format(r, v["Chassis"])] = {}
                output["{} : {}".format(r, v["Chassis"])]["FPC"] = [
                    vv for yy, vv in v["FPC"].items()
                ]
                output["{} : {}".format(r, v["Chassis"])]["SCB"] = [
                    vv for yy, vv in v["SCB"].items()
                ]

        if output:
            return output

    def hardware_info(self, verify_hardware):
        def get_info(host, model, yy, slots=0, exempt=False):
            fpcs = [v for v in yy["FPC"]]
            scbs = [v for v in yy["SCB"]]
            avail = slots - len(fpcs)
            if exempt:
                print()
                print(
                    bcolors.BOLD
                    + "     Hardware information for {}:".format(host.upper())
                    + bcolors.ENDC
                )
                print(bcolors.BOLD + "       Chassis: {}".format(model) + bcolors.ENDC)
            else:
                print()
                print(
                    bcolors.BOLD
                    + "   Hardware information for {}:".format(host.upper())
                    + bcolors.ENDC
                )
                print(bcolors.BOLD + "       Chassis: {}".format(model) + bcolors.ENDC)
                print(
                    bcolors.BOLD
                    + "       Slots available: {}".format(avail)
                    + bcolors.ENDC
                )
                print(
                    bcolors.BOLD
                    + "       Current FPC models: {}".format(", ".join(set(fpcs)))
                    + bcolors.ENDC
                )
                print(
                    bcolors.BOLD
                    + "       Current SCB models: {}".format("".join(set(scbs)))
                    + bcolors.ENDC
                )
                if avail > 0:
                    if "Enhanced MX SCB 2" in scbs:
                        print(
                            bcolors.OKGREEN
                            + "       MPC4E 3D 32XGE Linecard can be added (Line-rate throughput of up to 260 Gbps according to Juniper documentation)"
                            + bcolors.ENDC
                        )
                    elif "Enhanced MX SCB" in scbs:
                        print(
                            bcolors.WARNING
                            + "       MPC4E 3D 32XGE Linecard can be added (only 160Gb (16 ports) of line-rate throughput can be used due to overscription on {SCB})".format(
                                SCB="".join(set(scbs))
                            )
                            + bcolors.ENDC
                        )
                        print(
                            bcolors.OKGREEN
                            + "       MPC 3D 16x 10GE Linecard can be added utilizing current SCB({SCB})".format(
                                SCB="".join(set(scbs))
                            )
                            + bcolors.ENDC
                        )
                    elif "MX SCB" in scbs:
                        print(
                            bcolors.FAIL
                            + "       MPC4E 3D 32XGE Linecard can NOT be added (only 160Gb (16 ports) of line-rate throughput can be used due to overscription on {SCB})".format(
                                SCB="".join(set(scbs))
                            )
                            + bcolors.ENDC
                        )
                        print(
                            bcolors.WARNING
                            + "       MPC 3D 16x 10GE Linecard can be added (only utilizing 12 ports due to current SCB({SCB}) limitations".format(
                                SCB="".join(scbs)
                            )
                            + bcolors.ENDC
                        )
                    else:
                        print(
                            bcolors.WARNING
                            + "       No SCB/FPC info found for {} {}".format(
                                host, model
                            )
                            + bcolors.ENDC
                        )
                else:
                    print(
                        bcolors.FAIL
                        + "       No slots available on {}".format(host)
                        + bcolors.ENDC
                    )
            print()

        for y, yy in verify_hardware.items():
            if "MX240" in y:
                get_info(y.split(":")[0], "MX240", yy, slots=2)
            if "MX480" in y:
                get_info(y.split(":")[0], "MX480", yy, slots=6)
            if "MX960" in y:
                get_info(y.split(":")[0], "MX960", yy, slots=11)
            if "MX10003" in y:
                get_info(y.split(":")[0], "MX10003", yy, slots=0, exempt=True)
            if "PTX1000" in y:
                get_info(y.split(":")[0], "PTX1000 ", yy, slots=0, exempt=True)
            if "QFX5100" in y:
                get_info(y.split(":")[0], "QFX5100", yy, slots=0, exempt=True)
            if "QFX10002" in y:
                get_info(y.split(":")[0], "QFX10002", yy, slots=0, exempt=True)

    def br_agg_check_func(self, x, bars=None):
        print()
        print(
            bcolors.WARNING
            + "   [!] Checking if BR-AGG's are available for striping purposes.."
            + bcolors.ENDC
        )
        host = "".join({xx.split("-")[0] for xx in x})
        diff = set(BR_AGGS[host]) ^ set(x)
        if diff:
            print(
                bcolors.OKGREEN
                + "   Additional BR-AGG's are available for increased capacity (below)"
                + bcolors.ENDC
            )
            for v in sorted(diff):
                print("{:>21}".format(v))
            if BR_AGG_CHECK:
                print()
                print(
                    bcolors.BOLD
                    + "   Running port availability checks on BR-AGG's (displayed as LineCard/Ports):"
                    + bcolors.ENDC
                )
                _ = [
                    self.audit_port_avail(
                        vv, current_ports=None, requested=0, check="BR-AGG"
                    )
                    for vv in sorted(diff)
                ]
            print()
            if bars:
                print()
                print(
                    bcolors.BOLD
                    + "   Running port availability checks on VC-BAR's:"
                    + bcolors.ENDC
                )
                print(
                    bcolors.WARNING
                    + "      [*][*] Wiki for BR-AGG Scaling allocation/port-mapping information - https://w.amazon.com/bin/view/Main/Interconnect/DX_MPLSoUDP_HLD#HVC-BAR"
                    + bcolors.ENDC
                )
                print()
                _ = [
                    self.audit_port_avail(
                        d,
                        current_ports=None,
                        requested=len(diff),
                        check="VC-BAR",
                        lc_check=False,
                    )
                    for d in bars
                ]
        else:
            print(bcolors.FAIL + "   No additional BR-AGG's found" + bcolors.ENDC)

    def audit_port_avail(
        self, x: str, current_ports=None, requested=16, check=None, lc_check=True
    ):
        # /* Code for possible VC-BAR port reservations
        if "BFoot" in check:
            print(bcolors.BOLD + "      Info for {}:".format(x) + bcolors.ENDC)
            # count = portfunction.get_device_available_port(x)
            count = portfunction.get_device_available_port(x)
            ucount = {int(r) * len(v) / 1000: len(v) for r, v in count.items()}
            if ucount:
                logging.debug(ucount)
                for c, xx in ucount.items():
                    if xx + current_ports >= requested:
                        print(
                            "        {}: {} Ports Needed | {} Ports Available | {} Gb capacity available".format(
                                x, current_ports, xx, c
                            )
                        )
                    else:
                        print(
                            "        {}: {} Ports Needed | {} Ports Available | {} Gb capacity available | LINECARD-ADDITION-NEEDED".format(
                                x, current_ports, xx, c
                            )
                        )
                        verify_hardware = self.corr_info(x)
                        if verify_hardware:
                            logging.debug(verify_hardware)
                            self.hardware_info(verify_hardware)
                    print()
            else:
                print("        NSM Portfunction could not find any available ports")
        elif "VC-BAR" in check:
            print(bcolors.BOLD + "      Info for {}:".format(x) + bcolors.ENDC)
            forty_check = False
            count = portfunction.get_device_available_port(x)
            if count:
                count = {
                    "{}".format("40000" if "10000" in l else "10000"): list(
                        set([vv.split(":")[0] for vv in v])
                    )
                    for l, v in count.items()
                }
                threshold = 60 * requested
                inter_range = [
                    range(0, 3),
                    range(12, 15),
                    range(36, 39),
                    range(48, 51),
                ]
                qfx_ports = collections.defaultdict(list)

                for speed, interface in count.items():
                    if "40000" in speed or 40000 in speed:
                        forty_check = True
                    srt_inter = {
                        speed: sorted(interface, key=lambda x: int(x.split("/")[2]))
                    }
                for b in inter_range:
                    for rr, aa in srt_inter.items():
                        for a in aa:
                            check_intf = a.split("/")[2]
                            if int(check_intf) in b:
                                qfx_ports[rr].append(a)

                ucount = {int(r) * len(v) / 1000: len(v) for r, v in qfx_ports.items()}
                # print("\n".join(str(xx) for xx in qfx_ports.items()))
                for _, yy in qfx_ports.items():
                    print("      Available Ports for BR-AGG Scaling: {}".format(yy))
                #print()
                # for vv, ww in ucount.items():
                #    print("      Total Capacity (Including Capacity provided by breakout-cables) {}: {}".format(vv, ww))
                # print("\n".join(str(vv) for vv in ucount.items()))
                # print()
                for c, xx in ucount.items():
                    # if int(xx) >= int(threshold):
                    if forty_check:
                        print(
                            "        Ports Needed: {} | {} Ports Available ({} Ports available with breakout cable(s)) | {} Gb capacity available".format(
                                int(threshold / 10), xx, int(xx) * 4, c,
                            )
                        )
                    else:
                        print(
                            "        Ports Needed: {} | {} Ports Available | {} Gb capacity available".format(
                                int(threshold / 10), xx, c
                            )
                        )

                    verify_hardware = self.corr_info(x)
                    if verify_hardware:
                        logging.debug(verify_hardware)
                        self.hardware_info(verify_hardware)
                    # print()
        elif "BR-AGG" in check:
            print(bcolors.BOLD + "      Info for {}:".format(x) + bcolors.ENDC)
            # Port availabilty information for BR-AGG's
            def port_info(device_information):
                parse = [
                    (v, l["availability_state"])
                    for v, l in device_information["ports"].items()
                    if "AVAILABLE" in l["availability_state"]
                ]
                d = collections.defaultdict(list)
                for inter, info in parse:
                    key = inter.split()[0].split("/")[0].split("-")[1]
                    d[key].append(inter)
                return d

            device_information = portdata.get_full_device_info(x)

            for xx, yy in sorted(
                port_info(device_information).items(), key=lambda x: int(x[0])
            ):
                print("        {}: {}".format(xx, yy))
            print()

    def pre_hmbne(self):
        def br_agg_str_verify(x, *a, value=None):
            br_agg_neigh_check = False
            if "striping" in value:
                if len(x) < 4:
                    print(
                        bcolors.FAIL
                        + "  [!ALERT] BR-AGG striping is less than 4 devices"
                        + bcolors.ENDC
                    )
                    br_agg_neigh_check = True
                    root[self.name.split("-")[0]][self.name][
                        "{}".format(self.escape_ansi(self.design_type))
                    ][
                        "BR-AGG Striping (Min: 4 BR-AGG's)"
                    ] = "Fail ({} BR-AGG's found)".format(
                        len(x)
                    )
                else:
                    print(
                        bcolors.OKGREEN
                        + "   BR-AGG striping is within standard"
                        + bcolors.ENDC
                    )
                    root[self.name.split("-")[0]][self.name][
                        "{}".format(self.escape_ansi(self.design_type))
                    ][
                        "BR-AGG Striping (Min: 4 BR-AGG's)"
                    ] = "Success ({} BR-AGG's found)".format(
                        len(x)
                    )
                print("   BR-AGG peers are below:")
                for v in sorted(set(x)):
                    print("      {}".format(v))
                if br_agg_neigh_check:
                    self.br_agg_check_func(x)

        print()
        print(
            bcolors.UNDERLINE
            + "[*][*] {} [*][*]".format(self.name.upper())
            + bcolors.ENDC
        )
        print(bcolors.BOLD + "Northbound Capacity Info:" + bcolors.ENDC)
        print(self.design_type)
        if self.br_agg_agg_info:
            print(
                bcolors.WARNING
                + "1. Verifying VC-EDG <--> BR-AGG Capacity"
                + bcolors.ENDC
            )
            print(
                bcolors.BOLD + "  1A. VC-EDG to BR-AGG striping below:" + bcolors.ENDC
            )
            for h, c in dict(self.br_agg_agg_info).items():
                #/* Will be removed print("      {}: {}Gb".format(h, c))
                print("      {} --{}Gb--> {}".format(self.name, c, h))
            print("   Total capacity: {}Gb".format(self.br_agg_cap))
            print()
            root[self.name.split("-")[0]][self.name][
                "{}".format(self.escape_ansi(self.design_type))
            ]["VC-EDG to BR-AGG Capacity (Gb's)"] = self.br_agg_cap
        if self.br_agg_neighbors:
            print(bcolors.WARNING + "2. Verifying BR-AGG Striping" + bcolors.ENDC)
            br_agg_str_verify(set(self.br_agg_neighbors), value="striping")
        print()

    def Hmbv1_info(self):
        def hambone_v1_prnt(x, value=None):
            if "fab_to_bar" in value:
                bar_to_fab = collections.defaultdict(int)
                print(
                    bcolors.BOLD
                    + "  2A. VC-FAB to VC-BAR striping below:"
                    + bcolors.ENDC
                )
                for rr, tt in sorted(x.items()):
                    for r in tt:
                        for ww, qq in r.items():
                            print("      {} --{}Gb--> {}".format(rr, qq, ww))
                            bar_to_fab[ww] += int(qq)
                if bar_to_fab:
                    final = dict(bar_to_fab)
                    print()
                    print(
                        bcolors.BOLD
                        + " 2B. Aggregate VC-FAB to VC-BAR capacity below:"
                        + bcolors.ENDC
                    )
                    for x, y in final.items():
                        print("      {}: {}Gb".format(x, y))
                    total = sum([(float(y)) for _, y in final.items()])
                    print("     Total capacity to VC-BAR's: {}Gb".format(total))
                    print()
                    root[self.name.split("-")[0]][self.name][
                        "{}".format(self.escape_ansi(self.design_type))
                    ]["VC-FAB to VC-BAR Capacity (Gb's)"] = total
            if "bar_to_agg" in value:
                br_agg_check = ""
                bar_to_agg = []
                br_aggs = set()
                br_agg_neigh_check = False
                print(
                    bcolors.BOLD
                    + "  3A. VC-BAR to BR-AGG striping below:"
                    + bcolors.ENDC
                )
                for yy, xx in x.items():
                    for aa in xx:
                        a, b, c = aa[0], aa[1], aa[2]
                        if len(c) < 4:
                            br_agg_check = (
                                bcolors.FAIL
                                + "   [!ALERT] BR-AGG striping is less than 4 devices"
                                + bcolors.ENDC
                            )
                            br_agg_neigh_check = True
                            root[self.name.split("-")[0]][self.name][
                                "{}".format(self.escape_ansi(self.design_type))
                            ][
                                "BR-AGG Striping (Min: 4 BR-AGG's)"
                            ] = "Fail ({} BR-AGG's found)".format(
                                len(c)
                            )
                        else:
                            br_agg_check = (
                                bcolors.OKGREEN
                                + "   BR-AGG striping is within standard"
                                + bcolors.ENDC
                            )
                            root[self.name.split("-")[0]][self.name][
                                "{}".format(self.escape_ansi(self.design_type))
                            ][
                                "BR-AGG Striping (Min: 4 BR-AGG's)"
                            ] = "Success ({} BR-AGG's found)".format(
                                len(c)
                            )
                        for bb, band in sorted(c.items()):
                            print("      {} --{}--> {}".format(a, band, bb))
                            br_aggs.add(bb)
                        print("      {}: {}Gb".format(a, b))
                        print()
                        bar_to_agg.append(b)
                if bar_to_agg:
                    print()
                    print(
                        bcolors.BOLD
                        + "  3B. Aggregate VC-BAR to BR-AGG capacity below:"
                        + bcolors.ENDC
                    )
                    print(
                        "     Total capacity from VC-BAR's to BR-AGG's: {}Gb".format(
                            sum(bar_to_agg)
                        )
                    )
                    root[self.name.split("-")[0]][self.name][
                        "{}".format(self.escape_ansi(self.design_type))
                    ]["VC-BAR to BR-AGG Capacity (Gb's)"] = sum(bar_to_agg)
                if br_agg_check:
                    print()
                    print(
                        bcolors.WARNING + "4. Verifying BR-AGG Striping" + bcolors.ENDC
                    )
                    print(br_agg_check)
                    print("   BR-AGG peers are below:")
                    for v in sorted(br_aggs):
                        print("      {}".format(v))

                    if br_agg_neigh_check:
                        self.br_agg_check_func(br_aggs)

        print(
            bcolors.UNDERLINE
            + "[*][*] {} [*][*]".format(self.name.upper())
            + bcolors.ENDC
        )
        print(bcolors.BOLD + "Northbound Capacity Info:" + bcolors.ENDC)
        print(self.design_type)
        if self.vc_fab_agg_info:
            print(
                bcolors.WARNING
                + "1. Verifying VC-EDG <--> VC-FAB Capacity"
                + bcolors.ENDC
            )
            print(
                bcolors.BOLD + "  1A. VC-EDG to VC-FAB striping below:" + bcolors.ENDC
            )
            for h, c in dict(self.vc_fab_agg_info).items():
                #/* Will be removed print("      {}: {}Gb".format(h, c))
                print("      {} --{}Gb--> {}".format(self.name, c, h))
            print("   Total capacity: {}Gb".format(self.vc_fab_cap))
            print()
            root[self.name.split("-")[0]][self.name][
                "{}".format(self.escape_ansi(self.design_type))
            ]["VC-EDG to VC-FAB Capacity (Gb's)"] = self.vc_fab_cap
            if self.vc_bar_from_fab:
                print(
                    bcolors.WARNING
                    + "2. Verifying VC-FAB <--> VC-BAR Capacity"
                    + bcolors.ENDC
                )
                hambone_v1_prnt(self.vc_bar_from_fab, value="fab_to_bar")
                print()
            if self.vc_bar_from_border:
                print(
                    bcolors.WARNING
                    + "3. Verifying VC-BAR <--> BR-AGG Capacity"
                    + bcolors.ENDC
                )
                hambone_v1_prnt(self.vc_bar_from_border, value="bar_to_agg")
                # print(dict(out.vc_bar_from_border))
                print()

    def Hmbv2_info(self):
        def hambone_v2_prnt(x, value=None):
            # /* Keeping in script for possible migration scenarios */
            """
            if "fab_to_bar" in value:
                bar_to_fab = collections.defaultdict(int)
                print(bcolors.BOLD + "  2A. VC-FAB to VC-BAR striping below:" + bcolors.ENDC)
                for rr, tt in sorted(x.items()):
                    for r in tt:
                        for ww, qq in r.items():
                            print("      {} --{}Gb--> {}".format(rr, qq, ww))
                            bar_to_fab[ww] += int(qq)
                if bar_to_fab:
                    final = dict(bar_to_fab)
                    print()
                    print(
                        bcolors.BOLD
                        + " 2B. Aggregate VC-FAB to VC-BAR capacity below:"
                        + bcolors.ENDC
                    )
                    for x, y in final.items():
                        print("      {}: {}Gb".format(x, y))
                    total = sum([(float(y)) for _, y in final.items()])
                    print("     Total capacity to VC-BAR's: {}Gb".format(total))
                    print()
            """
            if "bar_to_agg" in value:
                br_agg_check = ""
                br_aggs = set()
                vc_bars = set()
                bar_to_agg = []
                br_agg_neigh_check = False
                print(
                    bcolors.BOLD
                    + "  2A. VC-BAR to BR-AGG striping below:"
                    + bcolors.ENDC
                )
                for yy, xx in x.items():
                    for aa in xx:
                        a, b, c = aa[0], aa[1], aa[2]
                        if len(c) < 4:
                            br_agg_check = (
                                bcolors.FAIL
                                + "   [!ALERT] BR-AGG striping is less than 4 devices"
                                + bcolors.ENDC
                            )
                            br_agg_neigh_check = True
                            root[self.name.split("-")[0]][self.name][
                                "{}".format(self.escape_ansi(self.design_type))
                            ][
                                "BR-AGG Striping (Min: 4 BR-AGG's)"
                            ] = "Fail ({} BR-AGG's found)".format(
                                len(c)
                            )
                            vc_bars.add(a)
                        else:
                            br_agg_check = (
                                bcolors.OKGREEN
                                + "   BR-AGG striping is within standard"
                                + bcolors.ENDC
                            )
                            root[self.name.split("-")[0]][self.name][
                                "{}".format(self.escape_ansi(self.design_type))
                            ][
                                "BR-AGG Striping (Min: 4 BR-AGG's)"
                            ] = "Success ({} BR-AGG's found)".format(
                                len(c)
                            )
                        for bb, band in sorted(c.items()):
                            print("      {} --{}--> {}".format(a, band, bb))
                            br_aggs.add(bb)
                        print("      {}: {}Gb".format(a, b))
                        print()
                        bar_to_agg.append(b)
                if bar_to_agg:
                    print()
                    print(
                        bcolors.BOLD
                        + "  2B. Aggregate VC-BAR to BR-AGG capacity below:"
                        + bcolors.ENDC
                    )
                    print(
                        "     Total capacity from VC-BAR's to BR-AGG's: {}Gb".format(
                            sum(bar_to_agg)
                        )
                    )
                    root[self.name.split("-")[0]][self.name][
                        "{}".format(self.escape_ansi(self.design_type))
                    ]["VC-BAR to BR-AGG Capacity (Gb's)"] = sum(bar_to_agg)
                if br_agg_check:
                    print()
                    print(
                        bcolors.WARNING + "3. Verifying BR-AGG Striping" + bcolors.ENDC
                    )
                    print(br_agg_check)
                    print("   BR-AGG peers are below:")
                    for v in sorted(br_aggs):
                        print("      {}".format(v))
                    if br_agg_neigh_check:
                        # self.audit_port_avail(
                        #     device,
                        #     current_ports=current_ports,
                        #     requested=16,
                        #     check="BFoot",
                        # )
                        self.br_agg_check_func(br_aggs, bars=vc_bars)

        print(
            bcolors.UNDERLINE
            + "[*][*] {} [*][*]".format(self.name.upper())
            + bcolors.ENDC
        )
        print(bcolors.BOLD + "Northbound Capacity Info:" + bcolors.ENDC)
        print(self.design_type)
        print()
        if self.vc_bar_agg_info:
            print(
                bcolors.WARNING
                + "1. Verifying VC-EDG <--> VC-BAR Capacity"
                + bcolors.ENDC
            )
            print(
                bcolors.BOLD + "  1A. VC-EDG to VC-BAR striping below:" + bcolors.ENDC
            )
            for h, c in dict(self.vc_bar_agg_info).items():
                #/* Will be removed print("      {}: {}Gb".format(h, c))
                print("      {} --{}Gb--> {}".format(self.name, c, h))
            print("   Total capacity: {}Gb".format(self.vc_bar_cap))
            print()
            root[self.name.split("-")[0]][self.name][
                "{}".format(self.escape_ansi(self.design_type))
            ]["VC-EDG to VC-BAR Capacity (Gb's)"] = self.vc_bar_cap
        if self.vc_bar_from_border:
            print(
                bcolors.WARNING
                + "2. Verifying VC-BAR <--> BR-AGG Capacity"
                + bcolors.ENDC
            )
            hambone_v2_prnt(self.vc_bar_from_border, value="bar_to_agg")
        print()

    def run_method(self):
        self.get_agg_info()
        self.get_bf_info()
        self.get_vc_info()
        self.hmb_check()


class BR_Device:
    def __init__(self, name):
        self.name = name
        # self.neigh = neigh
        self.interfaces = nsm_isd.get_raw_device(name)
        self.agg_links = [
            xx for xx in self.interfaces["interfaces"] if "physical" in xx["class"]
        ]
        self.br_info = []
        self.br_agg_info = collections.defaultdict(int)
        self.br_neighbors = []
        self.vc_cap = 0
        self.br_cap = 0
        self.bw_diff = 0

    def get_agg_info(self):
        # if not CACHE_CHECK[self.name]:
        if len(self.agg_links) > 1:
            device_info = [
                (
                    x["neighbors"]["link_layer"]["device_name"],
                    x["aggregation"]["name"],
                    x["bandwidth_mbit"],
                )
                for x in self.agg_links
                # if "vc-agg" in x["interface_description"].lower()
                if "br-agg" in x["interface_description"].lower()
                if "aggregation" in x and not "down" in x["status"]
                # /* Removed xe- check to crawl TITAN build sites */
                if "neighbors"
                in x  # and "xe-" in x["name"]  # To exclude Vegemite racks
            ]
            if device_info:
                # CACHE_CHECK.add(self.name)
                self.br_info = [x for x in device_info for y in x if "br-agg" in y]
                return (
                    self.name,
                    device_info,
                    self.br_info,
                )

    def get_br_info(self):
        if self.br_info:
            for l in self.br_info:
                self.br_agg_info[l[0]] += int(l[2]) / 1000
            self.br_neighbors = [x[0] for x in self.br_info]
            add_br = [int(x[2]) for x in self.br_info]
            self.br_cap = sum(add_br) / 1000
            return self.br_neighbors, self.br_cap

    def get_percent(self):
        if self.vc_cap > 1 and self.br_cap > 1:
            x = self.vc_cap
            y = self.br_cap
            self.bw_diff = x / y if x > y else y / x
            return self.bw_diff


def concurr_f(func, xx: list, *args) -> list:
    f_result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        vc_edg_final = {executor.submit(func, x, *args): x for x in xx}
        # vc_edg_final = {executor.submit(get_lag_info, x): x for x in xx}
        for future in concurrent.futures.as_completed(vc_edg_final):
            info = vc_edg_final[future]
            try:
                f_result.append(future.result())
            except Exception as e:
                pass
    return f_result if f_result else None


def get_lag_info(sp: str, capacity=160) -> dict:
    try:
        out = Device(sp, capacity)
        if out:
            methods_to_run = [out.run_method()]
        # /* Newly added BF checks */
        # if out.vc_cap > 1 and out.bf_cap > 1:
        #    device_info.append(
        #        (out.name, out.vc_cap, out.bf_cap, round(out.bw_diff, 2))
        #    )
        if "Pre-Hambone Design" in out.design_type:
            out.pre_hmbne()
        if "HamboneV1" in out.design_type:
            out.Hmbv1_info()
        if (
            "HamboneV2" in out.design_type
            or "Hambone migration project" in out.design_type
        ):
            out.Hmbv2_info()
        # /* Adding BF verification information
        if out.design_type:
            if out.bf_info and out.bf_cap:
                if out.design_type:
                    out.get_bfoot_info(
                        device=sp,
                        bf_info=out.bf_info,
                        bfoot_cap=out.bf_cap,
                        success=True,
                    )
            else:
                out.get_bfoot_info(success=False)
    except Exception as e:
        FAILED_DEVICE[sp] = "get_lag_info func {}".format(e)
        pass


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
    # /* Add list of BR-AGGs to defaultdict for membership test
    br_aggs = nsm.get_devices_from_nsm("br-agg", regions=region)
    if br_aggs:
        for br in br_aggs:
            BR_AGGS[br.split("-")[0]].append(br)
    # /* If AZ args specified then extract devices from specified AZ(s)
    if args.az:
        print(bcolors.HIGHGREEN + "AZ VERIFICATION ENABLED" + bcolors.ENDC)
        print(
            bcolors.HEADER
            + "THESE AZs WILL BE CHECKED: {}".format("".join(args.az))
            + bcolors.ENDC
        )
        print()
        # vc_edgs = [xx for xx in vc_edgs for a in args.az.split(",") if xx.startswith(a)]
        vc_edgs = [
            xx
            for xx in vc_edgs
            for a in args.az.split(",")
            if a in xx and len(a) == len(xx.split("-")[0])
        ]
        logging.debug(vc_edgs)
    if vc_edgs:
        vc_edg_final = concurr_f(get_lag_info, sorted(vc_edgs))
        vc_edg_final = list(filter(None.__ne__, vc_edg_final))
        if vc_edg_final:
            print()
            # print(vc_edg_final)
            c_devices = list(itertools.chain(*vc_edg_final))
            if c_devices:
                fmt_output(c_devices)
                print()
                audit_dict = get_port_info(c_devices)
                if audit_dict:
                    if args.cutsheet:
                        print(
                            bcolors.HIGHGREEN
                            + "Cutsheet generation is enabled"
                            + bcolors.ENDC
                        )
                        print(
                            bcolors.WARNING
                            + "These VC-EDG <--> Blackfoot cutsheets will need to be modified according to your situation"
                            + bcolors.ENDC
                        )
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
    print()
    logging.debug("Below is CACHE_CHECK dict")
    logging.debug(CACHE_CHECK)
    if root:
        print()
        print()
        print(
            bcolors.UNDERLINE
            + "[*][*]  Aggregated Information in JSON Dict  [*][*]"
            + bcolors.ENDC
        )
        formatted_json = json.dumps(
            root, sort_keys=True, indent=4, separators=(",", ": ")
        )
        colorful_json = highlight(
            formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()
        )
        print(colorful_json)
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

