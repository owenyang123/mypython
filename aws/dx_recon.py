#!/usr/bin/env python3.6

import argparse
import collections
import datetime
import heapq
import itertools
import logging
import math
import operator
import pprint
import random
import re
import signal
import sys
import textwrap
import time
import warnings

import numpy
from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.modules import maestro_db, nsm, jukebox
from dxd_tools_dev.portdata import border as portdata
from dxd_tools_dev.portdata import portfunction
from isd_tools_dev.modules import nsm as nsm_isd


VERSION = "0.07"


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


class CustomError(Exception):
    """Error in function"""

    def __init__(self, message, cause=None):
        """Initializer for Custom Function error handler

        :param str message: Error message
        :param cause: Exception that caused this error (optional)
        """
        super(CustomError, self).__init__(message)
        self.cause = cause


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
        "-p",
        "--phoenix",
        action="store_true",
        help="Enables assessment for Phoenix DX deployment",
        # default=False,
    )
    p.add_argument(
        "-c",
        "--centennial",
        action="store_true",
        help="Enables assessment for Centennial DX deployment",
        # default=False,
    )
    p.add_argument(
        "-b",
        "--bulkfiber",
        action="store_true",
        help="Enables line-card swap assessment if bulk-fiber is missing",
        # default=False,
    )
    return p.parse_args()


def intro_message():
    print()
    print(
        bcolors.HEADER
        + "###############################################################################"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###### Program will verify all pre-deployment assessment tasks (BETA)  ########"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###############################################################################"
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


class Legacy_VC_Info:
    def __init__(self, pop: str, bulk_fiber_override=False):
        self.vc_devices = []
        self.pop = pop
        self.bulk_fiber_override = bulk_fiber_override
        self.table = ddb.get_ddb_table("dx_devices_table")
        self.pop_table = ddb.get_ddb_table("tc_pop_border_capacity_table")
        self.pop_info = ddb.get_ddb_table("pop_size")
        self.pop_info_table = ddb.scan_full_table(self.pop_info)
        self.legacy_extract = {}
        self.port_status = {}
        self.device_information = {}
        self.customer_threshold_breach = False
        self.bgp_customer_threshold_breach = False

    def get_vc_devices(self) -> list:
        """Search existing PoP for VC Devices - return found devices

        Args:
            pop (str): PoP to be searched
        """
        region = jukebox.get_site_region_details(self.pop).region.realm
        a_devs_temp = nsm.get_devices_from_nsm("vc-car", regions=region)
        a_devs = [x for x in a_devs_temp if x.split("-")[0] == self.pop]
        self.vc_devices = a_devs

    def legacy_info(self):
        """ Populate legacy_extract dict with legacy information found on
        MX960's in specified PoP
        """
        car_hdware = {
            c: ddb.get_device_from_table(self.table, "Name", c)["Hardware"]
            for c in self.vc_devices
        }
        nine_six_info = {k: v for k, v in car_hdware.items() if "MX960" in v["Chassis"]}
        if len(nine_six_info) >= 1:
            self.legacy_extract.update(nine_six_info)

    def vc_port_info(self):
        swap_check_needed = True
        avail_fpc = False
        customer_threshold = 160
        bgp_threshold = 2800  # TODO: Verify this peer metric
        device_status = {k: True for k in self.legacy_extract}
        devices = len(device_status)
        ports = {
            k: ddb.get_device_from_table(self.table, "Name", k)["Interfaces"]
            for k in self.legacy_extract
        }
        # Customer-port threshold verification
        port_status = self.customer_port_count(ports, customer_threshold)
        if self.customer_threshold_breach:
            print()
            for k, v in sorted(
                port_status.items(), key=lambda x: int(x[0].split("-r")[1])
            ):
                if customer_threshold < v:
                    print(
                        f"   {k}: {bcolors.WARNING}Removing from assessment due to customer-count threshold breach {bcolors.ENDC}{bcolors.FAIL}Customer-facing connections: {v}{bcolors.ENDC}"
                    )
                    del self.legacy_extract[k]
                    device_status[k] = False
                    devices -= 1

        # Customer-facing BGP peer threshold verification
        bgp_status = self.customer_bgp_count(bgp_threshold)
        if self.bgp_customer_threshold_breach:
            print()
            for k, v in bgp_status.items():
                print(
                    f"   {k}: {bcolors.WARNING}Removing from assessment due to BGP peer threshold breach {bcolors.ENDC}{bcolors.FAIL}Customer-facing BGP peerings: {v}{bcolors.ENDC}"
                )
                # Add special check if k is in port_status
                if k in port_status:
                    del port_status[k]
                del self.legacy_extract[k]
                device_status[k] = False
                devices -= 1

        if devices >= 1:
            # If bulk-fiber override is enabled.. skip directly to checking for line-card swap
            if self.bulk_fiber_override:
                print()
                print(
                    f"   {bcolors.OKGREEN}[INFORMATIONAL]{bcolors.ENDC} Bulk-Fiber override check initiated for legacy VC-CAR's in {bcolors.WARNING}{self.pop}{bcolors.ENDC}\n      Will perform analysis on {devices} devices in {bcolors.WARNING}{self.pop}{bcolors.ENDC} to determine if existing 1Gb line-card(s) can be swapped"
                )
                self.onegb_fpc_info(port_status, ports, customer_threshold)
            else:
                # if MX960 (legacy VC-CAR hardware) - determine if any free FPC's are available for interim scaling solution
                empt_fpc_check = self.empty_fpc_check(self.legacy_extract)
                avail_fpc = any(len(v) >= 1 for k, v in empt_fpc_check.items())
                if avail_fpc:
                    print()
                    print(
                        f"   {bcolors.OKGREEN}[INFORMATIONAL]{bcolors.ENDC} Empty FPC's found in legacy VC-CAR's in {bcolors.WARNING}{self.pop}{bcolors.ENDC}\n      Will perform analysis on {devices} devices in {bcolors.WARNING}{self.pop}{bcolors.ENDC} to determine if empty FPC(s) can be used"
                    )
                    status = self.empt_fpc_info(empt_fpc_check, ports, port_status)
                    if status:
                        swap_check_needed = False
                if swap_check_needed:
                    print()
                    print(
                        f"   {bcolors.WARNING}[INFORMATIONAL]{bcolors.ENDC} No empty FPC's found in legacy VC-CAR's in {bcolors.WARNING}{self.pop}{bcolors.ENDC}\n      Will search {devices} devices in {bcolors.WARNING}{self.pop}{bcolors.ENDC} for 1Gb linecard(s) that could be replaced/swapped with 10Gb linecard(s)"
                    )
                    self.onegb_fpc_info(port_status, ports, customer_threshold)

                # else:
                #    print()
                #    print(
                #        f"   {bcolors.FAIL}[!ALERT]{bcolors.ENDC} All interim scaling options have been exhausted for legacy VC-CAR(s) in {bcolors.FAIL}{self.pop}{bcolors.ENDC}"
                #    )
                #     print()
                #     print(
                #         f"   {bcolors.OKGREEN}[INFORMATIONAL]{bcolors.ENDC} Empty FPC's found in legacy VC-CAR's in {bcolors.WARNING}{self.pop}{bcolors.ENDC}\n      Will perform analysis on {devices} devices in {bcolors.WARNING}{self.pop}{bcolors.ENDC} to determine if empty FPC(s) can be used"
                #     )
                #     self.empt_fpc_info(empt_fpc_check, ports, port_status)

        else:
            print()
            print(
                f"   {bcolors.FAIL}[!ALERT]{bcolors.ENDC} All interim scaling options have been exhausted for legacy VC-CAR(s) in {bcolors.FAIL}{self.pop}{bcolors.ENDC}"
            )

    def customer_port_count(self, ports: dict, c_thresh: int) -> dict:
        """ Discover VC devices that exceed customer-facing
        count threshold

        Args:
            ports (dict): dict of device port information

        Returns:
            dict: status output
        """
        status = {k: 0 for k in ports}
        threshold = c_thresh
        for x in status:
            cust_ports = [xx["Description"] for xx in ports[x]]
            filt_customer = [x for x in cust_ports if "customer" in x]
            if len(filt_customer) > threshold:
                self.customer_threshold_breach = True
            status[x] = len(filt_customer)
        return status

    def customer_bgp_count(self, threshold: int) -> dict:
        """ Discover VC devices that exceed BGP customer-facing
        peer threshold

        Args:
            threshold (int): customer-facing BGP peer threshold

        Returns:
            dict: status output
        """
        bgp_result = {}
        if len(self.legacy_extract) >= 1:
            try:
                device_check = {x for x in self.legacy_extract}
                extract = [x for x in self.pop_info_table if self.pop == x["PoP"]]
                for x in extract:
                    for k, v in x["CustBGPSessionInfo"].items():
                        host = k.split(".")[0]
                        if host in device_check and int(v) >= threshold:
                            self.bgp_customer_threshold_breach = True
                            bgp_result[host] = int(v)
            except KeyError:
                pass

        return bgp_result

    @staticmethod
    def tengb_count(ports: dict) -> dict:
        """ Count customer-facing 10Gb interfaces that are currently
            in use

            Args:
                ports (dict): interface information

            Returns:
                dict: aggregate count of 10Gb interfaces being used by customers
            """
        status = {k: 0 for k in ports}
        for x in status:
            tengb_ports = len(
                [
                    xx
                    for xx in ports[x]
                    if "customer" in xx["Description"] and "xe-" in xx["Name"]
                ]
            )
            status[x] = tengb_ports
        return status

    @staticmethod
    def empty_fpc_check(info: dict) -> dict:
        """ Search MX960's for empty FPC
        slots

        Args:
            info (dict): dict of FPC info

        Returns:
            dict: dict of empty FPC's
        """
        output = collections.defaultdict(set)
        fpc_status = {k: {"FPC 5", "FPC 7"} for k in info}
        for x, v in fpc_status.items():
            static_fpcs = {
                "FPC {}".format(xx) for xx in range(0, 12) if not "6" in str(xx)
            }
            fpc = sorted(info[x]["FPC"], key=lambda x: int(x.split(" ")[1]))
            v.update(fpc)
            intersect = static_fpcs - v
            output[x].update(intersect)
        return output

    @staticmethod
    def remove_anom(first: dict, second: dict, thresh_value=1) -> dict:
        """ Remove elements from dict that don't meet threshold

        Args:
            first (dict): dict to be modifed
            second (dict): dict that has threshold metric
            value (int, optional): threshold metric

        Returns:
            dict: return modified dict
        """
        problem_devices = []
        new = first
        for k, v in second.items():
            if v < thresh_value:
                if k in new:
                    problem_devices.append(k)
                    del new[k]
        return new, problem_devices

    def empt_fpc_info(self, fpc_devices: dict, ports: dict, info: dict):
        # SCB matrix found in https://code.amazon.com/packages/DXDeploymentTools/blobs/mainline/--/src/dxd_tools_dev/portdata/portmodel.py
        scb_lc_matrix = {
            "MX SCB": ("MPC 3D 16x 10GE", 12),
            "Enhanced MX SCB": ("MPC4E 3D 32XGE", 24),
            "Enhanced MX SCB 2": ("MPC4E 3D 32XGE", 26),
        }
        # Extract all VC-CAR's that have available FPC slots
        temp_fpc = {k: v for k, v in fpc_devices.items() if len(v) >= 1}
        # Extract Site info for PoP
        pop_info = ddb.get_device_from_table(self.pop_table, "Site", self.pop.upper())
        # Extract backhaul per VC-CAR
        pop_backhaul = self.backhaul_agg(pop_info)
        # Extract all VC-CAR's that don't have standard backhaul
        open_fpc, prb_devices = self.remove_anom(temp_fpc, pop_backhaul, thresh_value=1)
        # Extract total customer-facing capacity per VC-CAR
        cust_capacity = self.customer_port_agg(ports)
        # Extract SCB models from VC-CAR's that have available FPC slots
        scb_check = {
            k: "".join(set(self.legacy_extract[k]["SCB"].values())) for k in open_fpc
        }
        if len(open_fpc) >= 1:
            for k, v in open_fpc.items():
                print()
                print(f"      Router: {bcolors.WARNING}{k}{bcolors.ENDC}")
                print(
                    f"      FPC Info: {bcolors.WARNING}{len(v)}{bcolors.ENDC} FPC's empty"
                )
                print(
                    f"      Current customer-facing connections: {bcolors.WARNING}{self.customer_thresh(info[k])}{bcolors.ENDC}"
                )
                print(
                    f"      Current customer-facing capacity: {bcolors.WARNING}{cust_capacity[k]}{bcolors.ENDC} Gb"
                )
                print(
                    f"      Current border backhaul/capacity: {bcolors.WARNING}{pop_backhaul[k]}{bcolors.ENDC} Gb"
                )
                print(f"      SCB Model: {bcolors.WARNING}{scb_check[k]}{bcolors.ENDC}")
                print(
                    f"      Linecard Model that can be inserted into empty FPC(s): {bcolors.WARNING}{scb_lc_matrix[scb_check[k]][0]}{bcolors.ENDC}"
                )
                fpcs = [
                    l.replace("FPC ", "")
                    for l in sorted(v, key=lambda x: int(x.split()[1]), reverse=True)
                ]
                i = j = 0
                cust_count = cust_capacity[k]
                cust_add = 0
                while j <= len(fpcs) - 1:
                    cust_count += scb_lc_matrix[scb_check[k]][1] * 10
                    cust_add += scb_lc_matrix[scb_check[k]][1]
                    j += 1
                    print(f"         Option: {bcolors.WARNING}{j}{bcolors.ENDC}")
                    print(
                        f"         Adding linecard to FPC(s) {bcolors.WARNING}{', '.join(fpcs[i:j])}{bcolors.ENDC} will increase customer-facing capacity to: {bcolors.WARNING}{cust_count}{bcolors.ENDC} Gb"
                    )
                    new_cust_total = info[k] + cust_add
                    print(
                        f"            This would add {bcolors.WARNING}{cust_add}{bcolors.ENDC} 10Gb ports - bringing the customer-facing port total to: {self.customer_thresh(new_cust_total)}"
                    )
                    print(
                        f"            This will increase the potential customer/backhaul oversubscription ratio to {self.oversub_thresh(round(cust_count / pop_backhaul[k], 2))}"
                    )

                    # if j >= 3 and "32XGE" in scb_lc_matrix[scb_check[k]][0]:
                    #    print(
                    #        f"         {bcolors.WARNING}If you are adding more then three MPC4E 3D 32XGE's to an MX960 - be vigilant and double-check the power contraints on the device{bcolors.ENDC}"
                    #    )
                    # return True
        else:
            print(
                f"      {bcolors.WARNING}[!]{bcolors.ENDC} The devices below appear to have non-standard backhaul (might be a customer-specific setup) - skipping to next step(s):"
            )
            if len(prb_devices) >= 1:
                for p in prb_devices:
                    print(f"          {bcolors.FAIL}{p}{bcolors.ENDC}")
            return False
        return True

    def onegb_fpc_info(self, info: dict, ports: dict, cust_thresh: int) -> dict:
        """ Search MX960's for 1Gb linecards that could potentially 
        be swapped for 10Gb linecards

            Args:
                info (dict): dict of FPC info

            Returns:
                dict: dict of empty FPC's
        """
        swap_bool = False
        collect_total = collections.defaultdict(dict)
        collect_used = collections.defaultdict(dict)
        # Extract devices that have customer connection over threshold (160) - they will not be in scope
        temp_devices = {k: v for k, v in info.items() if v < cust_thresh}
        # Extract Site info for PoP
        pop_info = ddb.get_device_from_table(self.pop_table, "Site", self.pop.upper())
        # Extract backhaul per VC-CAR
        pop_backhaul = self.backhaul_agg(pop_info)
        # Extract VC-CAR's with non-standard backhaul
        srch_devices, _ = self.remove_anom(temp_devices, pop_backhaul, thresh_value=1)
        cust_capacity = self.customer_port_agg(ports)
        scb_check = {
            k: set(self.legacy_extract[k]["SCB"].values()) for k in srch_devices
        }
        for x in srch_devices:
            # Create dict for total 1Gb interfaces
            onegb_total = collections.defaultdict(list)
            # Create dict ofr 1Gb interfaces being used by customers
            onegb_used = collections.defaultdict(list)
            for xx in ports[x]:
                if "ge-" in xx["Name"]:
                    ident = xx["Name"].split("-")[1].split("/")[0]
                    onegb_total[ident].append(xx["Name"])
                    if "customer" in xx["Description"] or "up" in xx["Status"]:
                        onegb_used[ident].append(xx["Name"])
            # Count # of 1Gb interfaces on FPC
            count_total = {k: len(v) for k, v in onegb_total.items()}
            # Count # of 1Gb interfaces being used per FPC
            count_ints = {k: len(v) for k, v in onegb_used.items()}
            # Use heapsort to extract two FPC's with smallest customer port count
            n_small = heapq.nsmallest(2, count_ints.items(), operator.itemgetter(1, 0))
            # kp[0] is FPC and k[1] is number of 1Gb ports on FPC
            dict_add = {k[0]: k[1] for k in n_small}
            # Update used dictionary
            collect_used[x] = dict_add
            # Update agg dictionary
            collect_total[x] = count_total

        for v in collect_used:
            # verifies that dict contains at least two items
            if len(collect_used[v]) >= 2:
                # Max number of 1Gb ports that can be migrated off of an existing 1Gb LC
                threshold = 6
                # Max ports to use on 10Gb LC that will be swapped for
                new_ports = 24 if "Enhanced MX SCB" in "".join(scb_check[v]) else 12
                # k1 = 1Gb linecard that will potentially be swapped -- k2 = linecard that will absorb the orphaned ports from k1
                k1, k2 = collect_used[v]
                # if k1 ports are less than threshold -- proceed to next option
                if (k1 and k2) and collect_used[v][k1] < threshold:
                    # if k1 + k2 total on k2 is below total cabled ports on 1Gb linecard AND total customer port threshold not exceeded - proceed
                    if (collect_used[v][k2] + collect_used[v][k1]) < collect_total[v][
                        k2
                    ] and info[v] + new_ports < cust_thresh:
                        swap_bool = True
                        print()
                        print(f"      Router: {bcolors.WARNING}{v}{bcolors.ENDC}")
                        print(
                            f"      Current customer-facing connections: {bcolors.WARNING}{self.customer_thresh(info[v])}{bcolors.ENDC}"
                        )
                        print(
                            f"      Current customer-facing capacity: {bcolors.WARNING}{cust_capacity[v]}Gb{bcolors.ENDC}"
                        )
                        print(
                            f"      Current border backhaul/capacity: {bcolors.WARNING}{pop_backhaul[v]}Gb{bcolors.ENDC}"
                        )
                        print(
                            f"         SCB Found: {bcolors.WARNING}{''.join(scb_check[v])}{bcolors.ENDC}"
                        )
                        print(
                            f"         FPC# Eligble to be swapped: {bcolors.OKGREEN}FPC {k1}{bcolors.ENDC}"
                        )
                        print(
                            f"         FPC# that would absorb ports from {bcolors.WARNING}FPC {k1}{bcolors.ENDC}: {bcolors.OKGREEN}FPC {k2}{bcolors.ENDC}"
                        )
                        print(
                            f"            # of Ports that would need to be migrated from {bcolors.WARNING}FPC {k1}{bcolors.ENDC} to {bcolors.WARNING}FPC {k2}{bcolors.ENDC}: {bcolors.WARNING}{collect_used[v][k1]} port(s){bcolors.ENDC}"
                        )
                        print(
                            f"              Total number of 1Gb ports on {bcolors.WARNING}FPC {k2}{bcolors.ENDC} after migration: {bcolors.WARNING}{collect_used[v][k2] + collect_used[v][k1]}{bcolors.ENDC}"
                        )
                        print(self.ten_gb_lc(new_ports, k1))
                        print(
                            f"         # of new 10Gb ports to be added on {bcolors.WARNING}FPC {k1}{bcolors.ENDC} after linecard swap: {bcolors.OKGREEN}{new_ports}{bcolors.ENDC}"
                        )
                        print(
                            f"         This will increase the potential customer/backhaul oversubscription ratio to {self.oversub_thresh(round((info[v] + new_ports) / pop_backhaul[v], 2))}"
                        )
                        print(
                            f"         Total Customer Ports after linecard swap: {self.customer_thresh(info[v] + new_ports)}"
                        )
        if not swap_bool:
            print()
            print(
                f"   {bcolors.FAIL}[!ALERT]{bcolors.ENDC} All interim scaling options have been exhausted for legacy VC-CAR(s) in {bcolors.FAIL}{self.pop}{bcolors.ENDC}"
            )

    @staticmethod
    def ten_gb_lc(count: int, fpc: str) -> str:
        if count > 12:
            return f"         10Gb Linecard model that will be inserted into FPC {bcolors.WARNING}{fpc}{bcolors.ENDC}: {bcolors.OKGREEN}MPC4E 3D 32XGE{bcolors.ENDC}"
        return f"         10Gb Linecard model that will be inserted into FPC {bcolors.WARNING}{fpc}{bcolors.ENDC}: {bcolors.WARNING}MPC 3D 16x 10GE{bcolors.ENDC}"

    @staticmethod
    def customer_thresh(i: int) -> str:
        if 80 >= i:
            return f"{bcolors.OKGREEN}{i}{bcolors.ENDC}"
        elif 80 < i <= 155:
            return f"{bcolors.WARNING}{i}{bcolors.ENDC}"
        elif i > 155:
            return f"{bcolors.FAIL}{i}{bcolors.ENDC}"
            # return f"{bcolors.FAIL}{i} (Customer-Count threshold will be breached soon) {bcolors.ENDC}"

    @staticmethod
    def oversub_thresh(i: float) -> str:
        if 8 > i:
            return f"{bcolors.OKGREEN}{i}:1{bcolors.ENDC}"
        elif 8 < i < 15:
            return f"{bcolors.WARNING}{i}:1{bcolors.ENDC}"
        elif i > 15:
            return f"{bcolors.FAIL}{i}:1{bcolors.ENDC}"

    @staticmethod
    def backhaul_agg(pop_info: dict) -> dict:
        pop_band = {}
        for x in pop_info["Devices_Bandwidth_Gbps"]:
            pop_band[x["Name"]] = int(x["Bandwidth_Gbps"])
        return pop_band

    @staticmethod
    def customer_port_agg(ports: dict) -> dict:
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


def vc_info(args) -> list:
    """ Extract information from legacy VC devices/customer-facing
    port threshold information and return a dict with information to be used
    for border-device searching purposes

    Args:
        x (list): list of VC devices to search
    """
    pop = args.locator
    fiber_check = True if args.bulkfiber else False
    phx_check = False if args.centennial else True
    print(
        bcolors.BOLD
        + "[*] Existing VC-CAR Assessment in {} [*]".format(pop)
        + bcolors.ENDC
    )
    if phx_check:
        car_info = Legacy_VC_Info(pop, bulk_fiber_override=fiber_check)
        car_info.get_vc_devices()
        car_info.legacy_info()
        car_info.vc_port_info()
    if args.centennial:
        car_info = Legacy_VC_Info(pop, bulk_fiber_override=fiber_check)
        car_info.get_vc_devices()
    return car_info.vc_devices


def main():
    intro_message()
    now_time = datetime.datetime.now()
    args = parse_args()
    if args:
        car_devices = vc_info(args)
        # TODO: if not VC-CAR's are found in PoP - add logic to find border devices
        # print(car_devices)
    else:
        print("Need PoP option")
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


