#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import subprocess
import argparse

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
 
 
print("starting...")
class csDB:
    FETCH_CONSOLE_COMMAND = "ssh -tqA nebastion-iad " \
                                "/apollo/env/NRETools/bin/console.py -d {device} -r {region} | grep {device}"
 
    def request(self, device, region):
        bastion = None
        console = None
        port = None
        cmd = self.FETCH_CONSOLE_COMMAND.format(device=device, region=region)
        p = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
 
        stdout, stderr = p.communicate()
 
        if stdout:
            response = stdout.decode()
            words = response.split()
            if len(words) == 5:
                __device , __source, bastion, console, port = words
 
        return bastion, console, port
 
def get_console_db(device, region):
    """
 
    :param device:
    :param region:
    :return:
        bastion, console, port (string)
    """
    return csDB().request(device, region)
 
def get_device_list_from_regex(reg):
    """
 
    :param reg: icn54-54-vc-edg-r21[0-1]
                pls use "[]" include the start and end id
                 and use "-" split start id and end id
 
    :return:
    """
    result = list()
    if "[" not in reg:
        return [reg]
    prefix, rest = reg.split("[")
    range = rest.strip("]")
    start_str, end_str = range.split("-")
    start = int(start_str)
    end = int(end_str)
    i = start
    while i <= end:
        device = prefix + str(i)
        result.append(device)
        i += 1
    return result
 
 
def run_other_script(cmd):
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
 
    stdout, stderr = p.communicate()
    print("The following is the output of the script")
    print(stdout.decode())
 
 
 
def main():
    parser = argparse.ArgumentParser(description='show and config devices via console')
    parser.add_argument('-d', '--device_regex', help='give new product vc-edg name or regex, e.g. icn54-54-vc-edg-r211 or icn54-54-vc-edg-r21[0-1]  pls use "[]" include the start and end id and use "-" split start id and end id', required=True)
    parser.add_argument('-r', '--region', help='give region name, e.g. bjs', required=True)
    parser.add_argument('-B', '--bastion', help='give bastion name, e.g. consoles.bjs12')
    parser.add_argument('-S', '--show_file', help='file with show command list, with each cmd in a line')
    parser.add_argument('-L', '--log_file', help='file with record the log and output, default is ~/console-log-devicename-TIMESTAMP.log')
    parser.add_argument('-SDR', '--set_default_route',
                        help='set default router from interface vme.0 ',
                        action="store_true")
 
 
    args = parser.parse_args()
    region = args.region
    cmd = "/apollo/env/DXDeploymentTools/bin/cs.py -N -r {}".format(region)
 
    if args.show_file:
        cmd += " -S {} ".format(args.show_file)
    if args.log_file:
        cmd += " -L {} ".format(args.log_file)
    if args.set_default_route:
        # cmd += " -SDR {} ".format(args.set_default_route)
        cmd += " -SDR "
 
    bastion = None
    if args.bastion:
        bastion = args.bastion
 
    devices = get_device_list_from_regex(args.device_regex)
    print("the regex of {} includes the following devices:".format(args.device_regex))
    print(devices)
    for device in devices:
        print(bcolors.WARNING, "### console DB info for {} ###".format(device), bcolors.ENDC)
        db_bastion, console, port = get_console_db(device=device,region=region)
        if not bastion:
            bastion = db_bastion
        command = cmd + " -P {port} -CS {console} -d {device} -B {bastion}".format(port=port, console=console, device=device, bastion=bastion)
        print("running '{}'".format(command))
        run_other_script(command)
if __name__ == '__main__':
    main()