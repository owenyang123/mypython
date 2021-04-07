#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import argparse
import collections
import concurrent.futures
import itertools
import logging
import operator
import signal
import textwrap

import tqdm
from dxd_tools_dev.modules import nsm
from isd_tools_dev.modules import nsm as nsm_isd

# Enables quick termination of script if needed
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # IOError: Broken Pipe'}',
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C'}',

# Enables logging to be activated based on tags
logging.basicConfig(
    format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S", level=logging.INFO
)
logging.debug("Logging enabled")

CATCH_ERR = []
BRD_DEVICES = set()


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
        "-v",
        "--vc_type",
        help="Specify VC device type",
        type=str,
        nargs="?",
        default="vc-car",
        required=True,
    )
    p.add_argument(
        "-b",
        "--br_type",
        help="Specify BR device type",
        type=str,
        nargs="?",
        default="br-tra",
        required=True,
    )
    return p.parse_args()


def time_indic(items, region):
    logging.debug(
        bcolors.UNDERLINE
        + "[DEBUG INFO] !!!!!! Running LAG check against {} items in {} !!!!!!....".format(
            items, region.upper()
        )
        + bcolors.ENDC
    )


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


def get_lag_info(sp, dev_type="br-tra"):
    out = collections.defaultdict(list)
    new = collections.defaultdict(set)
    failed_devices = {}
    try:
        inter = nsm_isd.get_raw_interfaces_for_device(sp)
        pre_agg_links = [
            xx
            for xx in inter
            if "physical" in xx["class"]
            and "up" in xx["admin_status"]
            and dev_type in xx["interface_description"].lower()
        ]
        phys_links = [x for x in pre_agg_links if "neighbors" in x]
        device_info = [
            (
                xx["bandwidth_mbit"],
                xx["aggregation"]["name"],
                xx["neighbors"]["link_layer"]["device_name"].lower(),
            )
            for xx in phys_links
            if dev_type in xx["interface_description"].lower()
        ]

        o = sorted(device_info, key=operator.itemgetter(2))
        for s in o:
            if "br-tra" in dev_type:
                BRD_DEVICES.add(s[2])
            out[s[2]].append((int(s[0]), s[1], sp))

        for d, i in out.items():
            total = sum(ii[0] for ii in i)
            for xx in i:
                new[d].add((total, xx[1], xx[2]))

        if new:
            return dict(new)
    except Exception as e:
        failed_devices[sp] = "Failed due to {}".format(e)
    if failed_devices:
        CATCH_ERR.append(failed_devices)


def combine_dict(arg):
    test = collections.defaultdict(list)
    for d in arg:
        for key, value in d.items():
            x = list(itertools.chain(*value))
            test[key].append(x)
    return test


def kickoff_func(args):
    issues = False
    vc_cars = nsm.get_devices_from_nsm(args.vc_type, regions=args.region)
    br_tras = nsm.get_devices_from_nsm(args.br_type, regions=args.region)

    if vc_cars and br_tras:
        # time_indic(len(vc_cars) + len(br_tras), region)
        print(
            bcolors.WARNING
            + "Finding information for {} devices".format(args.vc_type)
            + bcolors.ENDC
        )
        vc_car_final_updated = concurr_f(get_lag_info, vc_cars, dev_type=args.br_type)
        print()
        # Adding border devices that may have not been find in initial NSM check
        if BRD_DEVICES:
            diff = list(set(BRD_DEVICES) - set(br_tras))
            if diff:
                print(
                    bcolors.OKGREEN
                    + "Additional {} devices have been found -- adding to list".format(
                        args.br_type
                    )
                    + bcolors.ENDC
                )
                br_tras.extend(diff)
                print()
        print(
            bcolors.WARNING
            + "Finding information for {} devices".format(args.br_type)
            + bcolors.ENDC
        )
        br_tra_final_updated = concurr_f(get_lag_info, br_tras, dev_type=args.vc_type)
        print()
        br_tra_final, vc_car_final = (
            list(filter(None.__ne__, br_tra_final_updated)),
            list(filter(None.__ne__, vc_car_final_updated)),
        )
        test_vc = combine_dict(br_tra_final)
        test_br = combine_dict(vc_car_final)
        if test_vc and test_br:
            for b, i in sorted(test_vc.items(), reverse=True):
                for ii in i:
                    if test_br[ii[2]]:
                        for xx in test_br[ii[2]]:
                            if b == xx[2]:
                                if ii[0] != xx[0]:
                                    issues = True
                                    print(
                                        bcolors.FAIL
                                        + "Unequal LAG(s) Found"
                                        + bcolors.ENDC
                                    )
                                    print(
                                        "A-Device: {} B-Device: {} A-Device Capacity: {}Gb B-Device Capacity: {}Gb A-Device AE: {} B-Device AE: {}".format(
                                            b,
                                            ii[2],
                                            int(int(ii[0]) / 1000),
                                            int(int(xx[0]) / 1000),
                                            xx[1],
                                            ii[1],
                                        )
                                    )
        if not issues:
            print(
                bcolors.OKGREEN
                + "No Unequal LAG(s) Found between {} devices and {} devices in {}".format(
                    args.vc_type, args.br_type, args.region
                )
                + bcolors.ENDC
            )


def main():
    args = parse_args()
    print(
        bcolors.UNDERLINE
        + "[DEBUG INFO] !!!!!! Running LAG check against devices in the following region(s):"
        + bcolors.ENDC
    )
    print(bcolors.WARNING + "{}".format(args.region.upper()) + bcolors.ENDC)
    print()
    if args:
        kickoff_func(args)
    print()
    if CATCH_ERR:
        print(bcolors.WARNING + "These devices had access issues" + bcolors.ENDC)
        print(bcolors.FAIL + "\n".join(str(v) for v in CATCH_ERR) + bcolors.ENDC)


if __name__ == "__main__":
    main()

