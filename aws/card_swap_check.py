#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

""" Short script that will verify if a 1Gb LC can be swapped for a 10Gb LC.  Below is output of script:
    network-config-builder-62002.pdx2% /apollo/env/DXDeploymentTools/bin/card_swap_check.py -d "hkg1-vc-car-hkg-r1,hkg1-vc-car-hkg-r2" -c 5
    ####################################################################################
    ###### Script to verify if VC devices have 1Gb LC(s) eligible to be swapped ########
    ####################################################################################

    Time script started: 2020-04-23 17:26


    Device(s) that will be checked:
        HKG1-VC-CAR-HKG-R1
        HKG1-VC-CAR-HKG-R2


    Port/Hardware Information being gathered for hkg1-vc-car-hkg-r1
        No empty 1Gb FPC's found.. verifying if ports can be migrated..
        FPC slot #'s below have 5 or less ports and are eligible for migration to another FPC (FPC with least # of ports in use will be migrated):
            FPC#: 4  Number of Ports in Use: 1
            FPC#: 8  Number of Ports in Use: 1
            FPC#: 9  Number of Ports in Use: 1
        FPC slot #'s below have 5 or more ports available and can accept migrated ports from another FPC:
            FPC#: 3  Available Ports: 21
            FPC#: 4  Available Ports: 39
            FPC#: 9  Available Ports: 39

        Checking Hardware Information for hkg1-vc-car-hkg-r1
            Hardware Model: MX960
            SCB type: Enhanced MX SCB 2
            MX960 model discovered - due to power contraints on this model additional verification will be performed..
            MPC4E 3D 32XGE Linecard can be inserted into FPC 8 (No power constraints found)

    Port/Hardware Information being gathered for hkg1-vc-car-hkg-r2
        No empty 1Gb FPC's found.. verifying if ports can be migrated..
        FPC slot #'s below have 5 or less ports and are eligible for migration to another FPC (FPC with least # of ports in use will be migrated):
            FPC#: 4  Number of Ports in Use: 1
            FPC#: 8  Number of Ports in Use: 1
            FPC#: 9  Number of Ports in Use: 1
        FPC slot #'s below have 5 or more ports available and can accept migrated ports from another FPC:
            FPC#: 3  Available Ports: 20
            FPC#: 8  Available Ports: 39
            FPC#: 9  Available Ports: 39

        Checking Hardware Information for hkg1-vc-car-hkg-r2
            Hardware Model: MX960
            SCB type: Enhanced MX SCB 2
            MX960 model discovered - due to power contraints on this model additional verification will be performed..
            MPC4E 3D 32XGE Linecard can be inserted into FPC 4 (No power constraints found)

    Script Time Stats:
    The script took 0 minutes and 16 seconds to run.
"""

import argparse
import collections
import datetime
import itertools
import operator
import textwrap
import time

from dxd_tools_dev.datastore import ddb

# Status dictionary that will verify issues
STATUS = {
    "DX Scaling Constraint": True,
}


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


def intro_message(message):
    print(
        bcolors.HEADER
        + "####################################################################################"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "###### Script to verify if VC devices have 1Gb LC(s) eligible to be swapped ########"
        + bcolors.ENDC
    )
    print(
        bcolors.HEADER
        + "####################################################################################"
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
    print("")
    print(bcolors.WARNING + "Device(s) that will be checked:" + bcolors.ENDC)
    for v in message.split(","):
        print("\t{}".format(str(v.strip().upper())))
    # print("\n".join(str(v.strip().upper()) for v in message.split(",")))
    print("")


def parse_args() -> str:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
    Script verifies if 1Gb LC can be swapped for 10Gb LC on a VC device.
    Usage:
        * python3 card_swap-2.py -d "icn50-vc-car-r1, icn50-vc-car-r2" -c 5
    """
        ),
    )
    p.add_argument(
        "-d",
        "--devices",
        help="comma separated list of devices",
        type=str,
        default="lax3-vc-car-r1, lax3-vc-car-r2",
    )
    p.add_argument(
        "-c",
        "--count",
        help="Maximum ports that could be migrated to enable card swap",
        type=int,
        default=5,
    )
    p.add_argument(
        "-o",
        "--override",
        action="store_true",
        help="override DX customer scaling constraints",
        # default=False,
    )
    return p.parse_args()


def tpm_message(devices: list) -> str:
    d = devices.split(",")[0]
    locator = d.split("-")[0]
    print()
    print()
    print(bcolors.HEADER + "\t   ** PLEASE READ MESSAGE BELOW **" + bcolors.ENDC)
    print(
        bcolors.WARNING
        + "If you haven't already.. please consult with your TPM about fiber infrastructure availability in {}".format(
            locator
        )
        + bcolors.ENDC
    )
    print(
        bcolors.WARNING
        + "If fiber infrastructure is available in {} and can accommodate a line-card addition -- please pursue that route".format(
            locator
        )
        + bcolors.ENDC
    )
    print(
        bcolors.WARNING
        + "instead of swapping a 1Gb line-card for a 10Gb line-card"
        + bcolors.ENDC
    )


def status_check(s: dict, devices: str):
    for r, b in s.items():
        if "DX Scaling Constraint" in r:
            if not b:
                print()
                print(
                    bcolors.FAIL
                    + "Line-card swap may violate DX scaling restraints -- More information: https://w.amazon.com/bin/view/Interconnect/ScalingConstraints/#BGP_Metrics"
                    + bcolors.ENDC
                )
                print(
                    bcolors.BOLD
                    + 'To override this constraint please re-run script and add "--override" to the cli options'
                    + bcolors.ENDC
                )
                print(
                    f'\t{bcolors.WARNING}Example: {bcolors.ENDC}card_swap_check.py -d "{devices}" --override'
                )


def hardware_info(d: str, avail_fpc: str, hware: dict):
    print()
    print(
        bcolors.BOLD + "\tChecking Hardware Information for {}".format(d) + bcolors.ENDC
    )
    sixteen_ten = False
    thirtytwo_ten_over = False
    thirtytwo_ten_nover = False
    fpc = ", ".join(str(x) for x in avail_fpc)
    # hware = nsm.get_device_hardware_from_nsm(d)
    if hware:
        print("\t\tHardware Model: {}".format("".join(hware["Chassis"])))
        scb = hware["SCB"]
        scbinfo = ",".join(set([y for _, y in scb.items()]))
        if any(x == "MX SCB" for x in scbinfo.splitlines()):
            print("\t\tSCB type: {}".format(scbinfo))
            sixteen_ten = True
        elif any(x == "Enhanced MX SCB" for x in scbinfo.splitlines()):
            print("\t\tSCB type: {}".format(scbinfo))
            thirtytwo_ten_over = True
        elif any(x == "Enhanced MX SCB 2" for x in scbinfo.splitlines()):
            print("\t\tSCB type: {}".format(scbinfo))
            thirtytwo_ten_nover = True

        if sixteen_ten:
            print(
                bcolors.WARNING
                + "\t\tDue to SCB contraints you can only insert a MPC 3D 16x 10GE into FPC {}".format(
                    fpc
                )
                + bcolors.ENDC
            )
        elif thirtytwo_ten_over or thirtytwo_ten_nover:
            if "MX960" in "".join(hware["Chassis"]):
                threshold = 0
                print(
                    bcolors.WARNING
                    + "\t\tMX960 model discovered - due to power contraints on this model additional verification will be performed.."
                    + bcolors.ENDC
                )
                time.sleep(2.0)
                fpc_info = {int(v.split()[1]): x for v, x in hware["FPC"].items()}
                for f, c in fpc_info.items():
                    if f in range(0, 6) and "32XGE" in c:
                        threshold += 1
                if threshold > 4:
                    if int(fpc) < 6:
                        print(
                            "\t\tDue to power constrains you can only insert a MPC 3D 16x 10GE into FPC {}".format(
                                fpc
                            )
                        )
                else:
                    if thirtytwo_ten_over:
                        print(
                            bcolors.WARNING
                            + "\t\tMPC4E 3D 32XGE Linecard can be swapped into FPC {} (No power constraints found) - Due to SCB model line-rate throughput will be limited".format(
                                fpc
                            )
                            + bcolors.ENDC
                        )
                    elif thirtytwo_ten_nover:
                        print(
                            bcolors.OKGREEN
                            + "\t\tMPC4E 3D 32XGE Linecard can be swapped into FPC {} (No power constraints found)".format(
                                fpc
                            )
                            + bcolors.ENDC
                        )


def car_cap_verify(hostname: str, p: dict, ddb_hware: dict) -> bool:
    """ Verify potential line-card addition won't violate DX scaling restraints
    https://w.amazon.com/bin/view/Interconnect/ScalingConstraints/#BGP_Metrics
    """
    if len(p) >= 1:
        threshold = 145

        ints = {
            px["Name"]: (px["Description"], px["Status"])
            for y, x in p.items()
            for px in x
            if "customer" in px["Description"].lower()
        }
        customer_count = len(ints)
        if customer_count > threshold:
            print(
                bcolors.WARNING
                + "Linecard swap on {} may violate DX Scaling Restraints".format(
                    hostname
                )
                + bcolors.ENDC
            )
            print(
                f"\tCurrent Customer Count: {bcolors.FAIL}{customer_count}{bcolors.ENDC}"
            )
            STATUS["DX Scaling Constraint"] = False
            return False
        else:
            return True
    else:
        print(
            bcolors.WARNING
            + "No 1Gb interfaces found on {}({})".format(
                hostname, "".join(ddb_hware["Chassis"])
            )
            + bcolors.ENDC
        )
        return False


def interface_info(device: str, min_ports=5, override=False):
    print()
    print(
        bcolors.UNDERLINE
        + "Port/Hardware/Customer-Count Information being gathered for {}:".format(
            device
        )
        + bcolors.ENDC
    )
    migration = True
    migrate_fpcs = []
    if device:
        try:
            complete_card = False
            table = ddb.get_ddb_table("dx_devices_table")
            ddb_hware = ddb.get_device_from_table(table, "Name", device)["Hardware"]
            p = {device: ddb.get_device_from_table(table, "Name", device)["Interfaces"]}
            ints_collected = collections.defaultdict(list)
            ints_used = {}
            violate_check = True if override else car_cap_verify(device, p, ddb_hware)
            ints = {
                px["Name"]: (px["Description"], px["Status"])
                for y, x in p.items()
                for px in x
                if "None" and "ge-" in px["Name"]
            }

            if violate_check:
                for i, d in ints.items():
                    ints_collected[i.split("-")[1].split("/")[0]].append(d)

                if ints_collected:
                    avail_slots = [
                        i
                        for i, d in ints_collected.items()
                        if all("None" in dd[0] and "down" in dd[1] for dd in d)
                    ]
                    if avail_slots:
                        complete_card = True
                        print(
                            bcolors.OKGREEN
                            + "\tFPC slot #'s below have no exisiting customer connections and are eligible for card-swap (No customer migrations should be required):"
                            + bcolors.ENDC
                        )
                        for v in sorted(avail_slots):
                            print("\t\t{}".format(v))
                        # print("\n".join(str(v) for v in sorted(avail_slots)))
                    elif not complete_card:
                        print(
                            bcolors.WARNING
                            + "\tNo empty 1Gb FPC's found.. verifying if ports can be migrated.."
                            + bcolors.ENDC
                        )
                        time.sleep(2.0)
                        for fpc, info in ints_collected.items():
                            tally = len([i for i in info])
                            count = len(
                                [i for i in info if "None" in i[0] and "down" in i[1]]
                            )
                            """ ints_used dict output:
                            {'9': (5, 40, 35), '8': (6, 40, 34), '3': (17, 40, 23), '4': (10, 40, 30)}
                            """
                            ints_used[fpc] = (tally - count, tally, count)

                        if ints_used:
                            elig_swap_fpc = {
                                f: p[0]
                                for f, p in ints_used.items()
                                if p[0] <= min_ports
                            }
                            if elig_swap_fpc:
                                if len(elig_swap_fpc) > 1:
                                    print()
                                    print(
                                        bcolors.OKGREEN
                                        + "\tFPC slot #'s below have {} or less 1Gb ports and are eligible for migration to another FPC (FPC with least # of ports in use will be migrated):".format(
                                            min_ports
                                        )
                                        + bcolors.ENDC
                                    )
                                else:
                                    print()
                                    print(
                                        bcolors.OKGREEN
                                        + "\tFPC slot # below has {} or less 1Gb ports and are eligible for migration to another FPC:".format(
                                            min_ports
                                        )
                                        + bcolors.ENDC
                                    )
                                for xx, yy in sorted(elig_swap_fpc.items()):
                                    print(
                                        "\t\tFPC#: {}  Number of Ports in Use: {}".format(
                                            xx, yy
                                        )
                                    )
                                elig_srt = dict(
                                    sorted(
                                        elig_swap_fpc.items(),
                                        key=operator.itemgetter(1),
                                    )
                                )
                                for f in dict(itertools.islice(elig_srt.items(), 1)):
                                    migrate_fpcs.append(f)
                                    del ints_used[f]

                                elig_migr_fpc = {
                                    f: p[2]
                                    for f, p in ints_used.items()
                                    if p[2] >= min_ports
                                }
                                if elig_migr_fpc:
                                    print()
                                    print(
                                        bcolors.OKGREEN
                                        + "\tFPC slot #'s below have {} or more 1Gb ports available and can accept migrated ports from another FPC:".format(
                                            min_ports
                                        )
                                        + bcolors.ENDC
                                    )
                                    for xx, yy in sorted(elig_migr_fpc.items()):
                                        print(
                                            "\t\tFPC#: {}  Available Ports: {}".format(
                                                xx, yy
                                            )
                                        )
                                    # print("\n".join(str(v) for v in sorted(elig_migr_fpc)))
                                else:
                                    migration = False
                                    print(
                                        bcolors.FAIL
                                        + "\t[!!] NO FPC slot #'s have {} or more 1Gb ports available and cannot accept migrated ports from another FPC".format(
                                            min_ports
                                        )
                                        + bcolors.ENDC
                                    )
                            else:
                                migration = False
                                print(
                                    bcolors.FAIL
                                    + "\t[!!] NO FPC slot #'s have {} or less 1Gb ports and cannot be migrated to another FPC".format(
                                        min_ports
                                    )
                                    + bcolors.ENDC
                                )
                    else:
                        migration = False
                        print(
                            bcolors.WARNING
                            + "\tNo 1Gb linecards found that are candidates to be swapped"
                            + bcolors.ENDC
                        )
                if migration and migrate_fpcs:
                    hardware_info(device, migrate_fpcs, ddb_hware)
        except Exception as e:
            print(bcolors.BOLD + "{}".format(device) + bcolors.ENDC)
            print(bcolors.FAIL + "failed: {}".format(e) + bcolors.ENDC)
    else:
        print(bcolors.FAIL + "No device found" + bcolors.ENDC)


def main():
    now_time = datetime.datetime.now()
    args = parse_args()
    devices = args.devices
    if args:
        intro_message(devices)
        _ = [
            interface_info(d.strip(), min_ports=args.count, override=args.override)
            for d in devices.split(",")
        ]
        status_check(STATUS, devices)
        tpm_message(devices)
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

