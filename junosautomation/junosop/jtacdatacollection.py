from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell
from datetime import datetime as t
import subprocess
import argparse
import os
import re
import datetime

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='jtacdatacollectionk.py')
    main_parser.add_argument("-c", "--case", type=str, dest="casenumber", required=True, help="inputcasenumber")
    return main_parser.parse_args()

def get_data(days):
    cur=datetime.date.today()
    delta=datetime.timedelta(days=days)
    return str(cur-delta)
def get_boxname():
    name=""
    command = 'cli show configuration \|display inheritance no-comments \|display set \|match host-name '
    output=[i for i in os.popen(command).read().split(" ") if i!=""][-1]
    if output:return name+output
    return name

def main():
    cli_arguments = parse_args().casenumber
    folder_path="/var/tmp/"+cli_arguments
    try:
        os.mkdir(folder_path)
    except:
        print('Directory already existed')
    boxname="".join([i for i in get_boxname() if i.isalnum()])
    date="".join([i for i in get_data(0) if i.isalnum()])
    #get RSI
    command = 'cli -c ' +'\"request support information |no-more |save '+folder_path+'/'+'RSI_'+boxname+'_'+date+'\"'+' &'
    os.system(command)
    #get all log 
    command ='cli -c '+ '\"file archive source /var/log compress destination '+folder_path+'/'+'LOG_'+boxname+'_'+date+'.tgz'+'\"' +' &'
    print(command)
    os.system(command)
    return

if __name__ == '__main__':
    main()
