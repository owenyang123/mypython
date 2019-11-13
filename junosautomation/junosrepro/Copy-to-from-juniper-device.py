'''How to Run the script?
>>Make sure the Boxes are enabled for netconf
#set system services netconf ssh
-Define an inventory.txt file with the list of IP's the script will be run against
-Define the NUM_PROCESSES=2, "vi RC-Mount-Copy.py" to modify the NUM_PROCESSES 
if you want to execute the script in parellel on multiple devices, if you have a batch of 100 devices, the recommended number is 15
>>>Sample RUN from JTAC LAB<<<
yshaik@yshaik-ubuntu:~/script$ python3 RC-Mount-Copy.py
Enter file name:inventory.txt
Username:  root
SSH private key passphrase: 
Executing the RC copy script on to IP: 172.22.201.129
172.22.201.129: b'scp-test1.txt': 9 / 9 (100%)
Executing the RC copy script on to IP: 172.22.146.128
172.22.146.128: b'scp-test1.txt': 9 / 9 (100%)
Finished in 2.810117 sec.'''

#Import the necessary modules
from jnpr.junos import Device
from jnpr.junos.utils.scp import SCP
from jnpr.junos.utils.start_shell import StartShell
import hashlib, getpass, os, time, multiprocessing

filename = None
host = None
uname = None
pw = None

#Define the number for process-pooling, example 2 will run the script on 2 devices in parellel
NUM_PROCESSES=20   

if filename == None:
    filename = input("Enter file name:")

if uname == None:
    uname = input("Username:  ")

if pw == None:
    pw = getpass.getpass("SSH private key passphrase: ")


Server_checksum=hashlib.md5(open('/import/home/V533560/4200-RC-checksum.txt', 'rb').read()).hexdigest()
#print('File on Server_checksum is:', Server_checksum)

#defining a fuction which is inturn called in another function
def compare_checksum(host, dev):
    with StartShell(dev) as ss:
        try:
            b=ss.run('md5 /var/home/aprinja/12.3R12-S3.1-MOP-RC-f')
        except Exception as err:
            print ('Unable to calculate checksum:', err) 
        else:
            #Checksum lookup
            if b[0]:
                Local_checksum=b[1].split('\r\n')[1].split('=')[1].strip()
                if Server_checksum==Local_checksum:
                    print('The Checksum matches on: ',dev.facts['hostname'])
                else:
                    print('Checksums do not match on: ',dev.facts['hostname'])
            else:
                print("unable to calculate checksum on: ",dev.facts['hostname'])

#defining a SCP_test function which is calling the checksum function                
def SCP_test(host):        
    if not host.strip():
        return
    
    host = host.strip(os.linesep)
    
    try:
        dev = Device(host=host, user=uname, password=pw, port=22, attempts=3, auto_probe=15)
        dev.open()
    except Exception as err:
        print ('Unable to open connection to {}: {}'.format(host, err)) 
    else:
        dev.timeout = 30
        
        if dev.facts['vc_fabric'] == 'None':
            print("Skipping {} as EX in VC mode".format(dev.facts['hostname']))
            return
        
        try:
            sw_ver = dev.facts['junos_info']['fpc0']['text'].strip()
        except KeyError:
            print("Unable to determine Junos version")
            return

        if dev.facts['junos_info']['fpc0']['text'].strip() != "15.1R6-S2.1":
            print("Skipping {} as Junos ver is {}".format(dev.facts['hostname'], dev.facts['junos_info']['fpc0']['text']))
            return

        print('Starting RC copy process on: ', dev.facts['hostname'])    
        with SCP(dev, progress=True) as scp:
            try:
                scp.put("12.3R12-S3.1-MOP-RC-f", remote_path="/var/home/aprinja/") 
            except Exception as err:
                print('Unable to copy:', err)
            else:
                compare_checksum(host, dev)

#Define a main function which is calling the SCP function
def main():
    with open(filename) as f, multiprocessing.Pool(processes=NUM_PROCESSES) as process_pool:
        time_start = time.time()
        process_pool.map(SCP_test, f)
    
    print("Finished in %f sec."% (time.time() - time_start))  # Total time taken for the script to execute

#Run the script only if you are the main function
if __name__ == "__main__":
    main()
