#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

""" This script interfaces with the border and vc port scaling API's. Using command-line
    options to specify what type of devices need to be scaled as well as capacity that is needed per device.
    Script will automatically determine the capacity needed to meet the threshold that is requested (40Gb by default)
    and find the necessary ports on all devices that were specified (if no devices are specified the script will find all devices in PoP/AZ
    based on device-type specified)

    Examples of usage are below:

    * To scale specified CAR's and TRA's in LAX3 PoP:
        /apollo/env/DXDeploymentTools/bin/border_scaling.py -vd "lax3-vc-car-r1,lax3-vc-car-r2" -bd "lax3-br-tra-r3,lax3-br-tra-r4" -c 40 --cutsheet
             -vd: VC device names
             -bd: Border device names
              -c: Capacity needed for each VC <-> BR device peering
             --cutsheet: Generate cutsheet (.xlsx) file in home directory

    * To scale specified BAR's and AGG's in SFO8 AZ:
        /apollo/env/DXDeploymentTools/bin/border_scaling.py -vd "sfo8-vc-bar-r1,sfo8-vc-bar-r2" -bd "sfo8-br-agg-r1,sfo8-br-agg-r2" -c 60 --mcm
             -vd: VC device names
             -bd: Border device names
              -c: Capacity needed for each VC <-> BR device peering
             --mcm: Create MCM for scaling operation

    * To scale specified DAR's and TRA's in EWR53 PoP (and JFK1 TC):
        /apollo/env/DXDeploymentTools/bin/border_scaling.py -vd "ewr53-vc-dar-r1" -bd "jfk1-br-tra-r6" -c 100 --cutsheet
             -vd: VC device names
             -bd: Border device names
              -c: Capacity needed for each VC <-> BR device peering
             --cutsheet: Generate cutsheet (.xlsx) file in home directory
"""

import argparse
import collections
import csv
import datetime
import json
import itertools
import math
import operator
import pathlib
import platform
import pprint
import signal
import sys
import textwrap
import time
from os.path import basename

import requests

import pandas as pd
from bs4 import BeautifulSoup
from dxd_tools_dev.modules import (
    border_port_alloc,
    jukebox,
    mcm,
    mwinit_cookie,
    nsm,
    vc_port_alloc,
)
from dxd_tools_dev.datastore import ddb
from isd_tools_dev.modules import nsm as nsm_isd
from requests_kerberos import OPTIONAL, HTTPKerberosAuth

# Enables quick termination of module if needed
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',


VERSION = "1.09"


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
    Script automated border scaling using border_port_alloc and vc_port_alloc module(s)
    """
        ),
    )
    p.add_argument(
        "-c",
        "--capacity_requested",
        help="Amount of backhaul for each VC <-> Border peering that is being requested",
        type=int,
        default=40,
    )
    p.add_argument(
        "-a",
        "--allocation_type",
        help="type of scaling operation -- right now default is 'scaling'",
        type=str,
        default="Existing Scaling",
    )
    p.add_argument(
        "-bd",
        "--border_devices",
        help="comma separated list of devices",
        type=str,
        default=None,
    )
    p.add_argument(
        "-vd",
        "--vc_devices",
        help="comma separated list of devices",
        type=str,
        default=None,
    )
    p.add_argument(
        "-cs",
        "--cutsheet",
        action="store_true",
        help="Enables cutsheet generation",
        # default=False,
    )
    p.add_argument(
        "-m",
        "--mcm",
        action="store_true",
        help="Enables cutsheet generation",
        # default=False,
    )
    return p.parse_args()


def args_check(x, locator):
    print()
    print(
        bcolors.HEADER
        + "#########################################"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###### Border Auto-Scaling Script #######"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "#########################################"
        + bcolors.ENDC
    )
    print()
    print(bcolors.BOLD + "Verification checklist:" + bcolors.ENDC)
    if locator:
        print(f"AZ/PoP Verification: {bcolors.WARNING}{locator}{bcolors.ENDC}")
    if locator:
        print(
            f"Region Verification: {bcolors.WARNING}{get_region(locator)}{bcolors.ENDC}"
        )
    if x.capacity_requested:
        print(
            f"Capacity Requested: {bcolors.WARNING}{x.capacity_requested}Gb{bcolors.ENDC} (40Gb is default unless otherwise modified)"
        )
    print(f"Script Version: {bcolors.OKGREEN}{VERSION}{bcolors.ENDC}")
    print()


def rundown(args, locator, vc_d, br_d):
    print(
        bcolors.HEADER
        + "Brief rundown of work that will be performed when using this script:"
        + bcolors.ENDC
    )
    print(
        f"\t1. Find region associated with {bcolors.WARNING}{locator}{bcolors.ENDC} (using Jukebox API)"
    )
    print(
        "\t2. Discover devices for backhaul verification_check (if no devices are specified)"
    )
    print(
        f"\t3. Finding hardware models for {bcolors.WARNING}{vc_d}{bcolors.ENDC} and {bcolors.WARNING}{br_d}{bcolors.ENDC} devices in {bcolors.WARNING}{locator}{bcolors.ENDC}"
    )
    print(
        f"\t4. Obtaining backhaul capacity between {bcolors.WARNING}{vc_d}'s{bcolors.ENDC} and {bcolors.WARNING}{br_d}'s{bcolors.ENDC}"
    )
    print(
        f"\t5. Obtaining backhaul capacity differential between {bcolors.WARNING}{vc_d}'s{bcolors.ENDC} and {bcolors.WARNING}{br_d}'s{bcolors.ENDC}"
    )
    print(
        f"\t6. Auditing {bcolors.WARNING}{br_d}{bcolors.ENDC} devices for available ports"
    )
    print(
        f"\t7. Obtaining capacity on {bcolors.WARNING}{br_d}{bcolors.ENDC} devices needed to meet requested backhaul capacity: {bcolors.WARNING}{args.capacity_requested}Gb{bcolors.ENDC}"
    )
    print(
        f"\t8. Adding ports found on {bcolors.WARNING}{br_d}{bcolors.ENDC} devices to queue to be used for backahul scaling"
    )
    print(
        f"\t9. Finalize port allocation on {bcolors.WARNING}{br_d}{bcolors.ENDC} devices"
    )

    print(
        f"\t10. Auditing {bcolors.WARNING}{vc_d}{bcolors.ENDC} devices for available ports"
    )
    print(
        f"\t11. Obtaining capacity on {bcolors.WARNING}{vc_d}{bcolors.ENDC} devices needed to meet requested backhaul capacity: {bcolors.WARNING}{args.capacity_requested}Gb{bcolors.ENDC}"
    )
    print(
        f"\t12. Adding ports found on {bcolors.WARNING}{vc_d}{bcolors.ENDC} devices to queue to be used for backahul scaling"
    )
    print(
        f"\t13. Finalize port allocation on {bcolors.WARNING}{vc_d}{bcolors.ENDC} devices"
    )
    if args.cutsheet or args.mcm:
        print(
            f"\t14. Creating cutsheet to be used for scaling {bcolors.WARNING}{vc_d}'s{bcolors.ENDC} and {bcolors.WARNING}{br_d}'s{bcolors.ENDC}"
        )
        if args.mcm:
            print(
                f"\t15. Creating draft MCM to be used for scaling {bcolors.WARNING}{vc_d}'s{bcolors.ENDC} and {bcolors.WARNING}{br_d}'s{bcolors.ENDC}"
            )
            print(
                f"\t16. Attaching cutsheet to draft MCM to be used for scaling {bcolors.WARNING}{vc_d}'s{bcolors.ENDC} and {bcolors.WARNING}{br_d}'s{bcolors.ENDC}"
            )
            print("\t17. Perform final validation")
        else:
            print("\t15. Perform final validation")
    else:
        print("\t14. Perform final validation")
    print()
    print(
        bcolors.WARNING
        + "WARNING!! *** You May See Alerts and Warnings from NSM Below ***"
        + bcolors.ENDC
    )
    time.sleep(2.0)


def get_region(loc: str) -> str:
    """Extract region using PoP/AZ locator

    Args:
        loc (str): PoP/AZ locator

    Returns:
        str: extracted region
    """
    site_code = loc
    try:
        site_info = jukebox.get_site_region_details(site=site_code)
        region = site_info.region.realm
    except (RuntimeError, TypeError, NameError, KeyError):
        extract = "".join([l for l in site_code if l.islower()])
        region = nsm_isd.get_nsm_region_for_site(extract)
    return region


def create_dict(d: dict) -> dict:
    """Function to create dict containing interface(s) speed
    info for cutsheet processing

    Args:
        d (dict): Contains speed information for interface(s)

    Returns:
        dict: Speed is extracted for cutsheet purposes
    """
    new = {}
    for k, v in d.items():
        for vv in v:
            speed = str(int(vv.split(" -- ")[0]) // 1000)
            new[k] = speed
    return new


def cutsheet_gen(d: str, info: str, a_spd: dict, b_spd: dict) -> str:
    """Function to create CSV file that will be used for cutsheet
    generation at a later process in program

    Args:
        d (str): PoP/AZ locator
        info (str): Info to populate CSV file
        a_spd (dict): Used to identify interface speed
        b_spd (dict): Used to identify interface speed

    Returns:
        str: filename of CSV that was created
    """
    print()
    print(
        f"{bcolors.BOLD}3. Creating cutsheet for scaling operation in {d}:{bcolors.ENDC}"
    )
    home = str(pathlib.Path.home())

    vc = create_dict(a_spd)
    br = create_dict(b_spd)

    with open("{}/{}.csv".format(home, d), "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "a_hostname",
                "a_lag",
                "a_interface",
                "a_speed",
                "z_speed",
                "z_interface",
                "z_lag",
                "z_hostname",
            ]
        )
        for a in info.split("\n"):
            if a:
                writer.writerow(
                    [
                        a.split(",")[0],
                        a.split(",")[1],
                        a.split(",")[2],
                        "{}Gb".format(br[a.split(",")[0]]),
                        "{}Gb".format(vc[a.split(",")[5]]),
                        a.split(",")[4],
                        a.split(",")[3],
                        a.split(",")[5],
                    ]
                )
    if pathlib.Path("{}/{}.csv".format(home, d)).exists():
        return "{}/{}.csv".format(home, d)
    # return True


def convert_file(a_file: str, location: str) -> str:
    """Function to convert CSV file to xlsx for MUDA integration

    Args:
        a_file (str): csv file to be converted
        location (str): PoP/AZ locator

    Returns:
        str: name of xlsx file
    """
    name = a_file
    if len(name) >= 3:
        before = name
        after = "{}_border_scaling_V1.xlsx".format(name.split(".")[0])
        if after:
            print(
                f"   Attempting to convert {bcolors.OKGREEN}{before}{bcolors.ENDC} to {bcolors.OKGREEN}{after}{bcolors.ENDC}"
            )
            pd.read_csv(before, delimiter=",").to_excel(after, index=False)
            if pathlib.Path(after).exists():
                print(f"\t{bcolors.OKGREEN}{after}{bcolors.ENDC} has been created")
                return after
            else:
                print(f"\t{bcolors.FAIL}{after}{bcolors.ENDC} was NOT created")


def cookie_verify(func_to_decorate: str):
    """Decorator that verifies if HTTP cookie is valid

    Args:
        func_to_decorate (str): MCM creation function
    """

    def new_func(*original_args):
        print()
        print(
            "   Testing HTTP Cookie validity (below you will see HTTP cookie debug info)"
        )
        cookies = mwinit_cookie.get_midway_cookie_obj()
        if len(cookies) >= 9:
            return func_to_decorate(*original_args)
        else:
            print(
                f"   One (or more) issues found with {bcolors.FAIL}HTTP cookies{bcolors.ENDC}"
            )

    return new_func


###########################################################################################################################################
## @anudeept's code (START)
###########################################################################################################################################


def get_regex(vc_car_list, br_tra_list):
    """This function returns device regex 
    for vc-car & br-tra
    """
    # get vc/br device regex
    vc_regex_maker = [device.split("-")[-1] for device in vc_car_list]
    vc_regex_routers = "|".join(vc_regex_maker)
    vc_regex = set([device.split("-r")[0] for device in vc_car_list])
    vc_regex = list(vc_regex)
    vc_device_regex = "".join(vc_regex) + "-(" + vc_regex_routers + ")"

    br_regex_maker = [device.split("-")[-1] for device in br_tra_list]
    br_regex_routers = "|".join(br_regex_maker)
    br_regex = set([device.split("-r")[0] for device in br_tra_list])
    br_regex = list(br_regex)
    br_device_regex = "".join(br_regex) + "-(" + br_regex_routers + ")"
    return vc_device_regex, br_device_regex


@cookie_verify
def cutsheet_mcm(vc_car_l, br_tra_l):
    vc_car_list = vc_car_l
    br_tra_list = br_tra_l
    regex_creator = get_regex(vc_car_list, br_tra_list)
    vc_regex = regex_creator[0]
    peer_regex = regex_creator[1]

    print(bcolors.OKBLUE, f"   [Info] : Creating  cutsheet MCM", bcolors.ENDC)
    # mcm_creation("mcm_title_overview_cutsheet_scaling",'sfo5-vc-car-r[1234]','sfo5-br-tra-r[1234]',['sfo20-vc-car-r1','sfo20-vc-car-r2'],['sfo5-br-tra-r1','sfo5-br-tra-r2'])
    try:
        mcm_create = mcm.mcm_creation(
            "mcm_title_overview_cutsheet_scaling",
            vc_regex,
            peer_regex,
            vc_car_list,
            br_tra_list,
            "CR-12312",
        )
    except Exception as error:
        print(bcolors.FAIL, f"[Error] : {error}", bcolors.ENDC)

    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = "https://mcm.amazon.com/cms/" + mcm_id
    print(
        bcolors.OKGREEN,
        f"   [Info] : Successfully created MCM - {mcm_link}",
        bcolors.ENDC,
    )
    print()
    # dry-run steps,deploy commands
    mcm_steps = [
        {
            "title": "Review Cutsheet",
            "time": 10,
            "description": "Review attached cutsheet",
            "rollback": "NA",
        }
    ]

    # MCM Update:
    try:
        mcm.mcm_update(mcm_id, mcm_uid, mcm_overview, mcm_steps)
        return mcm_id
    except Exception as error:
        print(bcolors.FAIL, f"[Error] : {error}", bcolors.ENDC)

    print(
        bcolors.OKGREEN,
        f"   [Info] : MCM successfully updated - {mcm_link}",
        bcolors.ENDC,
    )


###########################################################################################################################################
## @anudeept's code (END)
###########################################################################################################################################


class MCMBaseException(Exception):
    pass


class UnknownMCM(MCMBaseException):
    pass


class MCM(object):
    def __init__(self, mcm_id, endpoint="https://mcm.amazon.com"):
        """Class to extract CSRF token and attach cutsheets to MCMs

        Args:
            mcm_id (str): ID of MCM that will need cutsheet attachment
            endpoint (str, optional): MCM URL - Defaults to "https://mcm.amazon.com".
        """
        self.endpoint = endpoint
        self.session = requests.Session()
        self.cookies = mwinit_cookie.get_midway_cookie_obj()
        self.kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
        self.friendly_id = mcm_id
        self._get_cm()
        self.session.headers.update(
            {"X-CSRF-Token": self.csrf_token, "Accept": "application/json"}
        )

    def _get_cm(self):
        url = self.endpoint + "/cms/" + self.friendly_id
        page = self.session.get(url, auth=self.kerberos_auth, cookies=self.cookies)
        soup = BeautifulSoup(page.text, "lxml")
        cm_uuid = soup.find(id="cm_uuid")
        status = soup.find(id="cm_status")
        if not cm_uuid:
            raise UnknownMCM('UUID not found for Friendly ID "%s"' % self.friendly_id)
        if not status:
            raise UnknownMCM(
                'MCM Status not found for Friendly ID "%s"' % self.friendly_id
            )
        self.uuid = cm_uuid
        self.status = status.get("value")
        self.csrf_token = soup.find("meta", attrs={"name": "csrf-token"}).get("content")
        if not self.uuid or not self.csrf_token:
            raise UnknownMCM('UUID not found for Friendly ID "%s"' % self.friendly_id)

    def get_cutsheet(self):
        url = (
            self.endpoint
            + "/attachments/get_attachments?parent_type=CM&parent_uuid="
            + self.uuid.get("value")
        )
        cutsheet_check = self.session.get(
            url, auth=self.kerberos_auth, cookies=self.cookies
        )
        output = json.loads(cutsheet_check.content.decode("utf8"))
        self.cutsheets = {
            l["file_name"]
            for l in sorted(output["attachments"], key=lambda x: x["last_updated_date"])
        }

    def upload(self, filename):
        url = self.endpoint + "/attachments/create_attachment"
        data = {"parent_type": "CM", "parent_uuid": self.uuid.get("value")}
        with open(filename, "rb") as fh:
            files = [("files[]", (basename(filename), fh))]
            response = self.session.post(url, data=data, files=files)

        response.raise_for_status()
        res = response.json()

        if "err_msg" in res:
            raise MCMBaseException(res["err_msg"])

        return res


def ae_lag_extract(info: str, side=None):
    lags = set()
    for a in info.split("\n"):
        if a:
            if "border" in side:
                lags.add(a.split(",")[1])
            if "vc" in side:
                lags.add(a.split(",")[3])
    return lags


def device_diff(exist_list, curr_a, curr_b, curr_filename):
    exist_devices = set()
    for x in exist_list:
        if "a_devices" in x:
            exist_devices.update(x["a_devices"])
        if "b_devices" in x:
            exist_devices.update(x["b_devices"])
        if "cutsheet_size" in x:
            exist_filelen = int(x["cutsheet_size"])

    curr_devices = set()
    curr_devices.update(curr_a)
    curr_devices.update(curr_b)
    curr_filelen = pathlib.Path(curr_filename).stat().st_size
    return curr_devices == exist_devices and math.isclose(
        curr_filelen, exist_filelen, abs_tol=5
    )


def ddb_information(**kwargs):
    site = kwargs["site"]
    scale_table = ddb.get_ddb_table("scaling-table")
    extract_projects = ddb.scan_full_table(scale_table)
    site_extract = [s for s in extract_projects if site in s["site"].lower()]
    print()
    print(
        f"{bcolors.BOLD}4. Creating MCM for scaling operation in {site}:{bcolors.ENDC}"
    )
    print(
        f"   Searching DynamoDB for existing information regarding {bcolors.WARNING}{site}{bcolors.ENDC}"
    )
    if site_extract:
        print(
            f"   Scaling project already initiated for {bcolors.WARNING}{site}{bcolors.ENDC}.. verifying if this is a duplicate effort"
        )
        create_verify = device_diff(
            site_extract, kwargs["a_devices"], kwargs["b_devices"], kwargs["cutsheet"]
        )
        if create_verify:
            print(
                f"   \tDevices and cutsheet file size appear to be identical - {bcolors.FAIL}Information will not be added to DynamoDB{bcolors.ENDC}"
            )
        else:
            print(
                f"   \tDevices and cutsheet file size are not identical - {bcolors.OKGREEN}Information will be added to DynamoDB{bcolors.ENDC}"
            )
        # in_progress = [s for s in site_extract if not s["completed"]]
        # if in_progress:
        #     for k, _ in in_progress[0].items():
        #         in_progress[0]
        #         attach_task = MCM(mcm_id=k["MCM"])
        #         if not "Complete" in attach_task.status:
        #             attach_task.get_cutsheet()
        #             if not set(filename) in attach_task.cutsheets:
        #                 attach_task.upload(filename)
        #             else:

    else:
        print(
            f"   \tThis appears to be a new scaling project - {bcolors.OKGREEN}Information will be added to DynamoDB{bcolors.ENDC}"
        )
        filename = kwargs["cutsheet"]
        mcm_ident = cutsheet_mcm(kwargs["a_devices"], kwargs["b_devices"])
        if mcm_ident:
            kwargs["MCM"] = mcm_ident
            attach_task = MCM(mcm_id=mcm_ident)
            attach_task.upload(kwargs["cutsheet"])
            print()
            print(
                f"   \tAttaching {bcolors.OKGREEN}{filename}{bcolors.ENDC} to {bcolors.OKGREEN}{mcm_ident}{bcolors.ENDC}"
            )
            kwargs["cutsheet_size"] = pathlib.Path(kwargs["cutsheet"]).stat().st_size
        filt = [k for k, v in kwargs.items() if v == None]
        if not filt:
            ddb.put_item_to_table(scale_table, kwargs)


def device_type(d: str, d_type=None) -> str:
    """Function to extract device type

    Args:
        d (str): comma-seperated device(s)
        d_type (str, optional): specified device type

    Returns:
        str: specific device-type found
    """
    success = False
    devices = {
        "vc-bar": False,
        "vc-car": False,
        "vc-cor": False,
        "vc-dar": False,
        "vc-ecr": False,
        "vc-edg": False,
        "br-agg": False,
        "br-kct": False,
        "br-tra": False,
    }
    d_list = d.split(",")
    for d in devices:
        if all(d in v in v for v in d_list):
            success = True
            return d

    if not success:
        print(f"\t{d_type} Device-Type Found:{bcolors.FAIL} FAIL{bcolors.ENDC}")
        print(
            "\tPlease specify a single class of devices to be scaled (Ex: VC-CAR devices and BR-TRA devices)"
        )
        print()
        sys.exit()


def car_temp_check(v: str):
    devices = set(v.split(","))
    output = devices.intersection(PROBLEM_CARS)
    if len(output) >= 1:
        print(
            f"The {bcolors.WARNING}VC-CAR's{bcolors.ENDC} below do not have port-availability information populated at this time (issue is being worked) - script will exit"
        )
        for x in output:
            print(f"\t{bcolors.FAIL}{x}{bcolors.ENDC}")
        print()
        sys.exit()


def vc_device_check(x, args, vc_t, br_t):
    # TODO: This is a very brittle function but extremely important - will need to be re-written
    cars = set()
    brd_devices = set()
    for b, v in x.items():
        for bb, _ in v.items():
            if vc_t in bb and br_t in b:
                cars.add(bb)
                brd_devices.add(b)
    return sorted(list(cars)), sorted(list(brd_devices))


def b_dev_bh(info, cap_requested):
    for h, l in info.items():
        print("      Backhaul numbers for {}:".format(h))
        for hh, ll in sorted(l.items(), key=lambda x: int(x[1])):
            if cap_requested > int(ll):
                print(f"\t  {hh}: {bcolors.WARNING}{int(ll)}Gb{bcolors.ENDC}")
            else:
                print(f"\t  {hh}: {bcolors.OKGREEN}{int(ll)}Gb{bcolors.ENDC}")


def b_dev_cdiff(info):
    for x in info:
        for h, l in x.items():
            print("      Backhaul capacity differential for {}".format(h))
            for hh, ll in sorted(l.items(), key=lambda x: int(x[1]), reverse=True):
                if int(ll) > 0:
                    print(f"\t  {hh}: {bcolors.FAIL}{int(ll)}Gb{bcolors.ENDC}")
                else:
                    print(f"\t  {hh}: {bcolors.OKGREEN}{int(ll)}Gb{bcolors.ENDC}")


def b_dev_hware(hw_brd, hw_vc, brd_dev_type, vc_dev_type, location):
    if len(hw_brd) >= 1 and len(hw_vc) >= 1:
        print()
        print(
            bcolors.BOLD
            + "Hardware information for {} is below:".format(location)
            + bcolors.ENDC
        )
        print(
            bcolors.WARNING
            + "   {} hardware models found:".format(brd_dev_type)
            + bcolors.ENDC
        )
        for h, m in hw_brd.items():
            print(f"\t  {h}: {bcolors.WARNING}{m}{bcolors.ENDC}")

        print()
        print(
            bcolors.WARNING
            + "   {} hardware models found:".format(vc_dev_type)
            + bcolors.ENDC
        )
        for h, m in hw_vc.items():
            print(f"\t  {h}: {bcolors.WARNING}{m}{bcolors.ENDC}")


def brdr_lag_verify(bt, vt, exist=None, new=None) -> dict:
    lag_info = {
        "Existing": True,
        "New": False,
    }
    if len(new) >= 1:
        print(
            f"   NEW PEERING(s) Found Between {bcolors.WARNING}{bt}{bcolors.ENDC} <> {bcolors.WARNING}{vt}{bcolors.ENDC} devices - Further information below:"
        )
        for x, y in sorted(dict(new).items()):
            for yy in sorted(y, key=lambda x: x.split("---")[2]):
                if "Exists" in yy.split("---")[2]:
                    print(
                        f"      {x} --{bcolors.WARNING}{yy.split('---')[1]}{bcolors.ENDC}--> {yy.split('---')[0]} - {bcolors.WARNING}Existing LAG will be used to satisfy new peering{bcolors.ENDC}"
                    )
                elif "New" in yy.split("---")[2]:
                    lag_info["New"] = True
                    lag_info["Existing"] = False
                    print(
                        f"      {x} --{bcolors.OKGREEN}{yy.split('---')[1]}{bcolors.ENDC}--> {yy.split('---')[0]} - {bcolors.OKGREEN}New LAG will be created to satisfy new peering{bcolors.ENDC}"
                    )
    return lag_info
    # TODO add information for existing LAG(s)


def vc_lag_verify(vt, bt, exist=None, new=None):
    if len(new) >= 1:
        print(
            f"   {bcolors.OKGREEN}NEW PEERING INFORMATION WILL NEED TO BE CREATED TO SATISFY THIS SCALING REQUEST{bcolors.ENDC} - Further information below:"
        )
        for x, y in sorted(dict(new).items()):
            for yy in sorted(y, key=lambda x: x.split("---")[0]):
                print(
                    f"      {x} --{bcolors.OKGREEN}{yy.split('---')[1]}{bcolors.ENDC}--> {yy.split('---')[0]}"
                )
    # TODO add information for existing LAG(s)


def visual_rundown(vc: list, brd: list, cap: int):
    devices = {}
    for v in vc:
        devices[v] = brd
    if len(devices) >= 1:
        print(
            f"{bcolors.BOLD}[{bcolors.OKGREEN}INFORMATIONAL{bcolors.ENDC}{bcolors.BOLD}] Below is a visualization of the striping work that will be performed in this script (if needed):{bcolors.ENDC}"
        )
        for a, b in devices.items():
            for bb in b:
                print(
                    f"   {a:>20s}  <--{bcolors.OKGREEN}{cap}Gb{bcolors.ENDC}-->  {bb:>10s}"
                )


def safety_verification(allocated_ports: dict):
    error_dict = collections.defaultdict(set)
    avail_ports = collections.defaultdict(list)
    devices = [l for l in allocated_ports]
    for x, y in allocated_ports.items():
        for _, v in y.items():
            avail_ports[x].extend(v)

    if avail_ports:
        check_ports = collections.defaultdict(set)
        used_ports = {v: nsm.get_device_interfaces_from_nsm(v) for v in devices}
        for k, vv in used_ports.items():
            for v in vv:
                if "up" in v["Status"] and ("xe-" in v["Name"] or "et-" in v["Name"]):
                    check_ports[k].add(v["Name"])
        for k, v in avail_ports.items():
            output = set(v).intersection(check_ports[k])
            if output:
                error_dict[k].update(output)

    return error_dict


def tra_kct_over(d: dict, location, n=2):
    flagged = {k: v for k, v in d.items() if v > int(n)}
    if not flagged:
        print(
            f"       No {bcolors.WARNING}BR-TRA{bcolors.ENDC} devices in {location} appear to be oversubscribed towards the BR-KCT's - {bcolors.OKGREEN}THIS IS GOOD{bcolors.ENDC}"
        )

    else:
        count = len(flagged)
        print(
            f"       {bcolors.WARNING}{count} BR-TRA{bcolors.ENDC} devices in {location} appear to be oversubscribed towards the BR-KCT's - {bcolors.FAIL}THIS COULD BE PROBLEMATIC{bcolors.ENDC}"
        )
        print(
            f"       Below are the {bcolors.WARNING}BR-TRA{bcolors.ENDC} devices and their oversubscription ratio towards the BR-KCT's:"
        )
        for d, r in sorted(flagged.items()):
            print(f"          {d}:   {bcolors.FAIL}{r}:1{bcolors.ENDC}")


def extract_locat(s: str) -> str:
    p = [l.split("-")[0] for l in s.split(",")][0]
    return p


def b_dev_verify(args):
    cutsheet = False
    MCM_create = False
    b_locator = extract_locat(args.border_devices)
    z_locator = args.vc_devices.split(",")[0].split("-")[0]
    args_check(args, b_locator)
    vc_dt = device_type(args.vc_devices, d_type="VC")
    br_dt = device_type(args.border_devices, d_type="Border")
    if "Existing Scaling" in args.allocation_type:
        rundown(args, b_locator, vc_dt, br_dt)
    print()
    if args.cutsheet:
        cutsheet = True
    if args.mcm:
        cutsheet = True
        MCM_create = True
    if args.vc_devices and args.border_devices and args.capacity_requested:
        a = args.vc_devices.split(",")
        b = args.border_devices.split(",")
        visual_rundown(a, b, args.capacity_requested)
    if "br-tra" in br_dt:
        b_dev_srch = border_port_alloc.TRA_Allocation(
            pop=b_locator,
            capacity_requested=args.capacity_requested,
            vc_devices=args.vc_devices,
            border_devices=args.border_devices,
        )
    elif "br-agg" in br_dt:
        b_dev_srch = border_port_alloc.AGG_Allocation(
            az=b_locator,
            capacity_requested=args.capacity_requested,
            vc_devices=args.vc_devices,
            border_devices=args.border_devices,
            border_device_type=br_dt,
            vc_device_type=vc_dt,
        )
    elif "br-kct" in br_dt:
        b_dev_srch = border_port_alloc.KCT_Allocation(
            pop=b_locator,
            capacity_requested=args.capacity_requested,
            vc_devices=args.vc_devices,
            border_devices=args.border_devices,
            border_device_type=br_dt,
            vc_device_type=vc_dt,
        )
    # For VC <> VC Device scaling vc_devices and border_devices are flipped
    elif "vc-dar" in br_dt:
        b_dev_srch = vc_port_alloc.DAR_Allocation(
            vc_devices=args.border_devices.split(","),
            border_devices=args.vc_devices.split(","),
            capacity_requested=args.capacity_requested,
        )
    # For VC <> VC Device scaling vc_devices and border_devices are flipped
    elif "vc-bar" in br_dt:
        b_dev_srch = vc_port_alloc.BAR_Allocation(
            vc_devices=args.border_devices.split(","),
            border_devices=args.vc_devices.split(","),
            capacity_requested=args.capacity_requested,
        )
    # For VC <> VC Device scaling vc_devices and border_devices are flipped
    elif "vc-cor" in br_dt:
        b_dev_srch = vc_port_alloc.COR_Allocation(
            vc_devices=args.border_devices.split(","),
            border_devices=args.vc_devices.split(","),
            capacity_requested=args.capacity_requested,
        )
    b_dev_srch.run_all()
    print()
    print(
        bcolors.BOLD
        + "1. Running port availability audit for {} devices in {}:".format(
            br_dt, b_locator
        )
        + bcolors.ENDC
    )
    if b_dev_srch.adequate_backhaul:
        print(
            f"   {br_dt} devices in {b_locator} meet requested capacity demands: {bcolors.OKGREEN}SUCCESS{bcolors.ENDC}"
        )
        print()
        print(
            bcolors.WARNING
            + "   Current backhaul capacity between {} and {} (in Gb's)".format(
                vc_dt, br_dt
            )
            + bcolors.ENDC
        )
        b_dev_bh(b_dev_srch.existing_vc_backhaul, args.capacity_requested)
    else:
        print(
            f"   {br_dt} devices in {b_locator} meet requested capacity demands: {bcolors.FAIL}FALSE{bcolors.ENDC}"
        )
        vc_dt = device_type(args.vc_devices, d_type="VC")
        br_dt = device_type(args.border_devices, d_type="Border")
        if b_dev_srch.existing_vc_backhaul:
            print(
                bcolors.WARNING
                + "   Below is the current capacity between {} and {} devices (in Gb's)".format(
                    vc_dt, br_dt
                )
                + bcolors.ENDC
            )
            b_dev_bh(b_dev_srch.existing_vc_backhaul, args.capacity_requested)
            print()
            print(
                bcolors.WARNING
                + "   Below is the capacity needed to satisfy request of {}Gb between {} and {} devices in {}".format(
                    args.capacity_requested, vc_dt, br_dt, b_locator
                )
                + bcolors.ENDC
            )
            b_dev_cdiff(b_dev_srch.existing_vc_cap_diff)
            print()
        else:
            # print()
            # print(
            #     bcolors.FAIL
            #     + "   No backhaul information found between {} and {} devices in {}. Exiting script now".format(
            #         vc_dt, br_dt, locator
            #     )
            #     + bcolors.ENDC
            # )
            print(
                f"   Scaling request for {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices in {b_locator} can be fulfilled: {bcolors.FAIL}FALSE{bcolors.ENDC}"
            )
            if len(b_dev_srch.failed_items) >= 1:
                print(
                    f"   Below are the {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices that had issues:"
                )
                for d, r in sorted(b_dev_srch.failed_items.items()):
                    print(f"      {d}:   {bcolors.FAIL}{r}{bcolors.ENDC}")
                print()
            sys.exit()
        if b_dev_srch.finalized_ports:
            if b_dev_srch.request_complete:
                print(
                    f"   Running safety check to verify that only {bcolors.OKGREEN}AVAILABLE{bcolors.ENDC} ports are being allocated for {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices in {b_locator} for scaling purposes"
                )
                safety_check = safety_verification(b_dev_srch.finalized_ports)
                if len(safety_check) >= 1:
                    print(
                        f"       Safety verification for {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices in {b_locator} has {bcolors.FAIL}FAILED{bcolors.ENDC}"
                    )
                    print(
                        f"   Below are the {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices (and ports) that were mistakenly allocated:"
                    )
                    for d, r in sorted(safety_check.items()):
                        print(f"      {d}:   {bcolors.FAIL}{r}{bcolors.ENDC}")
                    sys.exit()
                else:
                    print(
                        f"       Safety verification for {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices in {b_locator} has {bcolors.OKGREEN}SUCCEEDED{bcolors.ENDC}"
                    )
                # Adding BR-TRA <> BR-KCT informational oversubscription output
                if "br-tra" in br_dt and b_dev_srch.oversub_info:
                    print(
                        f"   Running check to verify that the {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices in {b_locator} are not oversubscribed towards the BR-KCT's"
                    )
                    tra_kct_over(b_dev_srch.oversub_info, b_locator)
                if b_dev_srch.existing_band_ae_per_vc:
                    print(
                        f"   Scaling request for {bcolors.WARNING}{br_dt.upper()}{bcolors.ENDC} devices in {b_locator} is fulfilled: {bcolors.OKGREEN}SUCCESS{bcolors.ENDC}"
                    )
                    if b_dev_srch.lag_exist or b_dev_srch.lag_new:
                        brd_lag_dict = brdr_lag_verify(
                            br_dt,
                            vc_dt,
                            exist=b_dev_srch.lag_exist,
                            new=b_dev_srch.lag_new,
                        )
                    print()
                    print(
                        bcolors.BOLD
                        + "2. Running port availability audit for {} devices in {}:".format(
                            vc_dt, z_locator
                        )
                        + bcolors.ENDC
                    )
                    vc_devices, brd_devices = vc_device_check(
                        b_dev_srch.finalized_ports, args, vc_dt, br_dt
                    )
                    if vc_devices and brd_devices:
                        if "vc-car" in vc_dt:
                            vc_output = vc_port_alloc.CAR_Allocation(
                                vc_devices=vc_devices,
                                border_devices=brd_devices,
                                capacity_requested=args.capacity_requested,
                            )
                        elif "vc-bar" in vc_dt:
                            vc_output = vc_port_alloc.BAR_Allocation(
                                vc_devices=vc_devices,
                                border_devices=brd_devices,
                                capacity_requested=args.capacity_requested,
                            )
                        elif "vc-edg" in vc_dt:
                            vc_output = vc_port_alloc.EDG_Allocation(
                                vc_devices=vc_devices,
                                border_devices=brd_devices,
                                capacity_requested=args.capacity_requested,
                            )
                        elif "vc-dar" in vc_dt:
                            vc_output = vc_port_alloc.DAR_Allocation(
                                vc_devices=vc_devices,
                                border_devices=brd_devices,
                                capacity_requested=args.capacity_requested,
                            )
                        elif "vc-cor" in vc_dt:
                            vc_output = vc_port_alloc.COR_Allocation(
                                vc_devices=vc_devices,
                                border_devices=brd_devices,
                                capacity_requested=args.capacity_requested,
                            )
                        vc_output.run_all()
                        if vc_output.request_complete:
                            print(
                                f"   Scaling request for {bcolors.WARNING}{vc_dt}{bcolors.ENDC} devices in {z_locator} can be fulfilled: {bcolors.OKGREEN}SUCCESS{bcolors.ENDC}"
                            )
                            if vc_output.lag_exist or vc_output.lag_new:
                                vc_lag_dict = brdr_lag_verify(
                                    vc_dt,
                                    br_dt,
                                    exist=vc_output.lag_exist,
                                    new=vc_output.lag_new,
                                )
                            print()
                            print(
                                bcolors.WARNING
                                + "   Below is CSV info needed for backhaul scaling"
                                + bcolors.ENDC
                            )

                            vc_out = ""
                            d = [l for l, _ in vc_output.border_cap_needed.items()]
                            for x in d:
                                try:
                                    for vc, ae in vc_output.existing_band_ae_per_vc[
                                        x
                                    ].items():
                                        for vcc, aee in vc_output.finalized_ports[
                                            x
                                        ].items():
                                            if (
                                                int(ae[0])
                                                < vc_output.capacity_requested
                                            ):
                                                if vc == vcc:
                                                    for aa in aee:
                                                        vc_out += "{},{},{},{}\n".format(
                                                            x, ae[1], aa, vc
                                                        )
                                except:
                                    print(
                                        "   !!!! {} needs to be manually verified".format(
                                            x
                                        )
                                    )
                                    pass

                            br_output = ""
                            dd = [l for l, _ in b_dev_srch.border_cap_needed.items()]
                            for x in dd:
                                try:
                                    for vc, ae in b_dev_srch.existing_band_ae_per_vc[
                                        x
                                    ].items():
                                        for (vcc, aee,) in b_dev_srch.finalized_ports[
                                            x
                                        ].items():
                                            if (
                                                int(ae[0])
                                                < b_dev_srch.capacity_requested
                                            ):
                                                if vc == vcc:
                                                    for aa in aee:
                                                        br_output += "{},{},{},{}\n".format(
                                                            x, ae[1], aa, vc
                                                        )
                                except:
                                    print(
                                        "   !!!! {} needs to be manually verified".format(
                                            x
                                        )
                                    )
                                    pass
                            vc_o = [v for v in vc_out.split("\n") if v]
                            br_out = [b for b in br_output.split("\n") if b]
                            hold = collections.defaultdict(list)
                            told = collections.defaultdict(list)
                            if vc_o and br_out:
                                for x in sorted(vc_o):
                                    hold[x.split(",")[0]].append(x.split(",", 1)[1])
                                for r in sorted(br_out):
                                    told[r.split(",")[-1]].append(r.split(",", 0)[0])
                            keys = [h for h in hold]
                            final_output = ""
                            print(
                                "a_hostname,a_lag,a_interface,z_lag,z_interface,z_hostname,action"
                            )
                            for aa in keys:
                                for b, a in zip(told[aa], hold[aa]):
                                    print(
                                        "{},{},{},{},{},{},added".format(
                                            a.split(",")[2],
                                            b.split(",")[1],
                                            b.split(",")[2],
                                            a.split(",")[0],
                                            a.split(",")[1],
                                            b.split(",")[3],
                                        )
                                    )
                                    final_output += "{},{},{},{},{},{},added\n".format(
                                        a.split(",")[2],
                                        b.split(",")[1],
                                        b.split(",")[2],
                                        a.split(",")[0],
                                        a.split(",")[1],
                                        b.split(",")[3],
                                    )
                            if cutsheet and final_output:
                                csv_create = cutsheet_gen(
                                    b_locator,
                                    final_output,
                                    vc_output.existing_band_type_per_vc,
                                    b_dev_srch.existing_band_type_per_vc,
                                )
                                if csv_create:
                                    print()
                                    print(
                                        f"   CSV file created: {bcolors.OKGREEN}{csv_create}{bcolors.ENDC}"
                                    )
                                    attach = convert_file(csv_create, b_locator)
                                    if attach and MCM_create:
                                        b_side = ae_lag_extract(
                                            final_output, side="border"
                                        )
                                        a_side = ae_lag_extract(final_output, side="vc")
                                        if a_side and b_side:
                                            ddb_information(
                                                site=b_locator,
                                                version="V1",
                                                MCM=None,
                                                a_devices=vc_devices,
                                                a_lags=list(a_side),
                                                b_lags=list(b_side),
                                                b_devices=brd_devices,
                                                capacity=args.capacity_requested,
                                                cutsheet=attach,
                                                cutsheet_size=None,
                                                completed=False,
                                                a_exist_lag=vc_lag_dict["Existing"],
                                                a_new_lag=vc_lag_dict["New"],
                                                b_exist_lag=brd_lag_dict["Existing"],
                                                b_new_lag=brd_lag_dict["New"],
                                            )
                            if final_output:
                                b_dev_hware(
                                    b_dev_srch.border_hardware,
                                    b_dev_srch.vc_hardware,
                                    br_dt,
                                    vc_dt,
                                    b_locator,
                                )
                        else:
                            print(
                                f"   Scaling request for {bcolors.WARNING}{vc_dt}{bcolors.ENDC} devices in {z_locator} can be fulfilled: {bcolors.FAIL}FALSE{bcolors.ENDC}"
                            )
                            if len(vc_output.failed_items) >= 1:
                                print(
                                    f"   Below are the {bcolors.WARNING}{vc_dt}{bcolors.ENDC} devices that had issues:"
                                )
                                for d, r in sorted(vc_output.failed_items.items()):
                                    print(
                                        f"      {d}:   {bcolors.FAIL}{r}{bcolors.ENDC}"
                                    )

                    else:
                        print(
                            bcolors.FAIL
                            + "Adequate number of {} and {} devices could not be found for port verification".format(
                                vc_dt, br_dt
                            )
                            + bcolors.ENDC
                        )
            else:
                # print(
                #     bcolors.WARNING
                #     + "   Scaling request is partially fulfilled -- Manual Verification Needed"
                #     + bcolors.ENDC
                # )
                print(
                    f"   Scaling request for {bcolors.WARNING}{br_dt}{bcolors.ENDC} devices in {z_locator} can be fulfilled: {bcolors.FAIL}FALSE{bcolors.ENDC}"
                )
                diff = set(b_dev_srch.finalized_ports) ^ set(
                    b_dev_srch.existing_band_ae_per_vc
                )

                if len(diff) >= 1:
                    print(
                        f"   {bcolors.WARNING}Below are the {br_dt} device(s) that cannot be scaled at this time:{bcolors.ENDC}"
                    )
                    for v in diff:
                        print(
                            f"\t   {v}: {bcolors.FAIL}Can't allocate required ports necessary for scaling request{bcolors.ENDC}"
                        )
                else:
                    print(
                        f"   {bcolors.WARNING}Below are the {br_dt} device(s) that cannot be scaled at this time:{bcolors.ENDC}"
                    )
                    for d, r in sorted(b_dev_srch.failed_items.items()):
                        print(f"      {d}:   {bcolors.FAIL}{r}{bcolors.ENDC}")

        else:
            print(
                f"   Scaling request for {bcolors.WARNING}{br_dt}{bcolors.ENDC} devices in {a_locator} can be fulfilled: {bcolors.FAIL}FALSE{bcolors.ENDC}"
            )
            if len(b_dev_srch.failed_items) >= 1:
                print(
                    f"   Below are the {bcolors.WARNING}{vc_dt}{bcolors.ENDC} devices that had issues:"
                )
                for d, r in sorted(b_dev_srch.failed_items.items()):
                    print(f"      {d}:   {bcolors.FAIL}{r}{bcolors.ENDC}")


def main():
    now_time = datetime.datetime.now()
    args = parse_args()
    if args:
        b_dev_verify(args)

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


