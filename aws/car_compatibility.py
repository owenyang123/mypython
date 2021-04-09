#VC CAR Template Compability Requirements
# 1. Provisioning disable must be AFTER BGP collection (pre-update)
# 2. Provisioning enable must be AFTER BGP collection/comparison (post-update)
# 3. System Traffic Checks must be DISABLED for VC-CAR's, as we can't control customer traffic.

### Usage ###
#$ car_compatability.py --t file_name.jt
# This is not compatible with Alfred(yaml) templates!

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--template','--t', help="The full directory to where the template resides")
args = parser.parse_args()

file_name = args.template
autochecks = ['provision.disableProvisioning','_bgp_before','_bgp_after', 'provision.enableProvisioning','netvane_checks.check_device_utilisation_is_below_threshold']
not_found_strings = []

def search_multiple_strings_in_file(file_name, autochecks):
    """Get line from the file along with line numbers, which contains any string from the list"""
    line_number = 0
    list_of_results = []
    with open(file_name, 'r') as read_obj:
        for line in read_obj:
            line_number += 1
            for autocheck in autochecks:
                if autocheck in line:
                    list_of_results.append((autocheck, line_number, line.rstrip()))
    return list_of_results


def main():
    print('\033[1;36;40m *** Retrieve Line Numbers in which Auto-checks exist, and ensure their order is correct ***')

    matched_lines = search_multiple_strings_in_file(file_name, autochecks)

    print('\033[1;32;40m\tAutoChecks Found : ', len(matched_lines))
    for elem in matched_lines:
        print('\033[0;32;40m AutoCheck Located = ', elem[0], ' :: Line Number = ', elem[1])
    print(f"\033[0;37;40m \n1. Provisioning disable must be AFTER BGP collection (pre-update)")
    print(f"\033[0;37;40m \n2. Provisioning enable must be AFTER BGP collection/comparison (post-update)")
    print(f"\033[0;37;40m \n3. System Traffic Checks must be DISABLED for VC-CAR's, as we can't control customer traffic.")
    print(" \033[0;37;40m \t3.1 Please check the template to ensure traffic check is disabled for VC-CAR")


if __name__ == '__main__':
    main()
