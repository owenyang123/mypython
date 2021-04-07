#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import subprocess
import time
import argparse
import pathlib
import os

#Example file for the andon cord list:
#cat examplefile.txt
#
#    ON4ZPI7B2QFCK4MWQNX3LE6BKLCNTNSN
#    NTLAOTQMZ53CLEQH5DXAIXZ3WQJTFVP
#    BUTAA4QIQGRZGC2WW2FRXHEGNNBHEGVW
#    DMFTCNXRZULRNVC5ZORQZUG6SFG25CBT
#    RV52ZYVMZTWMLLSHRXU42LBU5GJAHVLQ
#    NGB5LCNPQCPO4FPLXOQX5MUPNMAHYBHY
#    I5HVAFKCFYEHGL3KQQRGUDWNSRAVW2WI
#    XSUJQJ6NJHMRJEPCYI36URNIHXJREZFB
#    WAWCZD7TZ7NGL7VKGMGX7ZP2HNMWZTLJ
#    Z63GURRETCGAMIOAL2NPIJZ5MRHQCISX
#
#To see andon cords in which you've created, please visit https://w2.corp.amazon.com/bin/view/Networking/NFE-Analytics/ACCS/Dashboard
#At the bottom of that page, under "Andon Cord List", click "Show" to see all andon cords.


print("Andon Cord Removal Process")
def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='andon_batch_removal.py', description='Deletion of andon cords en mass via script')
    main_parser.add_argument("-r", "--region", action="store", dest="region", required=True, help="The 3-digit region code in which your andon cords are located")
    main_parser.add_argument("-f", "--filename", action="store", dest="filename", required=True, help="Filename for andon cord list")
    return main_parser.parse_args()

def check_andons(filename, region):
    username = os.getlogin()
    unowned = []
    global andons_owned
    if os.path.isfile(filename) == True:
        print(f"File validated: {filename}")
        print(f"Validating {username} owns the following Andon Cords")
        with open(filename, 'r') as f:
            output = [l.strip('\n') for l in f.readlines()]
            print(output)
        print()
    if len(output) >= 1:
        try:
            check_command = "/apollo/env/HerculesUtilitiesCLI/bin/hercules-utilities.sh " + region + " andon-cord list | grep " + username
            print(f"Executing {check_command}")
            check = subprocess.run(check_command,shell=True,check=True,universal_newlines=True,stdout=subprocess.PIPE)
            check_output = check.stdout
            print("\n" + check_output + "\n")
            for line in output:
                print(f"Checking ownership of {line}")
                if line in check_output:
                    print(f"Validated {username} owns Andon ID {line}")
                    andons_owned = True
                else:
                    unowned.append(line)
                    andons_owned = False
            if unowned:
                print("You do NOT own the following Andon ID's, and will not continue:")
                for c, v in enumerate(unowned, 1):
                    print(c, v)
                andons_owned = False
            else:
                andons_owned = True
        except:
            andons_owned = False
            print("You do not own any Andon Cords for this region!")
            print("Congratulations I guess")
            return andons_owned


def delete_andons(filename, region):
    print("Sanity Check Succeeded")
    failed = []
    with open (filename) as f:
        lines = f.readlines()
        for line in lines:
            command = "/apollo/env/HerculesUtilitiesCLI/bin/hercules-utilities.sh " + region + " andon-cord delete " + line
            print(f"Executing {command}")
            try:
                deletion = subprocess.run(command,shell=True,check=True,universal_newlines=True,stdout=subprocess.PIPE)
                print(f"Removing Andon Cord {line}")
                output = deletion.stdout
                print(output)
                print("Waiting 3 seconds before attempting the next deletion...")
                time.sleep(3)
            except:
                print(f"Error! Unable to remove Andon Cord {line} - Does it exist?")
                failed.append(line)
    if failed:
        print("The following andon cords were unable to be removed:")
        print(failed)
    else:
        print("All specified andon cords have been removed.")


def main():
    args = parse_args()
    home = str(pathlib.Path.home())
    filename = "{}/{}".format(home, args.filename)
    region = args.region
    if filename:
        check_andons(filename, region)
    if andons_owned:
            delete_andons(filename, region)


if __name__ == '__main__':
    main()
