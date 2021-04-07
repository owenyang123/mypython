#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import subprocess
from dxd_tools_dev.modules import jukebox
from dxd_tools_dev.modules.utils import setup_logging
import logging



def sostenuto_devices_to_configure(region):
    sostenuto_devices = jukebox.get_devices_in_jukebox_region(region)
    vc_car_list = []
    for device in sostenuto_devices:
        if 'car' in device:
            vc_car_list.append(device)
    return vc_car_list


def per_region(region):
    first_deployed_vc_car = [ ]
    vc_car_devices_per_region = []
    vc_car_devices_per_region = sostenuto_devices_to_configure(region)
    logging.info (" * * "+ region)
    for vc_car in vc_car_devices_per_region:
        logging.info("Checking {} ".format(vc_car))
        generate_config = subprocess.run ("/apollo/env/HerculesConfigDownloader/bin/hercules-config --user-log-level critical get --hostname {} latest --file set-config --uncensored | grep -c 'export TESTLOOP-1-DX-VPN-DATA-PLANE-ADVERTISEMENT' ".format (vc_car ), stdout=subprocess.PIPE,shell=True )
        output=generate_config.stdout.decode('ascii').splitlines()
        if output[0] == "1":
            logging.info("First Deployed cars: ")
            first_deployed_vc_car.append(vc_car)
            y = vc_car[ :-1 ]+str ( int ( vc_car[ -1 ] )+1 )
            first_deployed_vc_car.append ( y )
            logging.info ( first_deployed_vc_car )
            break



def all_regions():
    first_deployed_vc_car = [ ]
    for i,region in enumerate(realm):
        logging.info (str ( i+1 )+" - "+ region)
        vc_car_devices = sostenuto_devices_to_configure( region )
        for j,vc_car in enumerate(vc_car_devices):
            logging.info("Checking {} ".format(vc_car))
            generate_config = subprocess.run ("/apollo/env/HerculesConfigDownloader/bin/hercules-config --user-log-level critical get --hostname {} latest --file set-config --uncensored | grep -c 'export TESTLOOP-1-DX-VPN-DATA-PLANE-ADVERTISEMENT' ".format (vc_car ), stdout=subprocess.PIPE,shell=True )
            output=generate_config.stdout.decode('ascii').splitlines()
            if output[0] == "1":
                logging.info("First Deployed cars: ")
                first_deployed_vc_car.append(vc_car)
                y = vc_car[ :-1 ]+str ( int ( vc_car[ -1 ] )+1 )
                first_deployed_vc_car.append ( y )
                logging.info ( first_deployed_vc_car )
                first_deployed_vc_car = [ ]
                break
def main():
    setup_logging ()
    realm = ["iad","sfo","pdx","gru","dub","nrt","sin","syd","cmh","yul","arn","fra","kix","cdg","lhr","bah","hkg","bom","icn"]
    userinput = str(input ( "you want first deployed VC-CAR for all regions or specific one (Enter all OR your region (iad,pdx,....): " ))
    
    if userinput.lower()== "all":
        all_regions()
    elif userinput.lower() == "iad":
        per_region("iad")
    elif userinput.lower() == "sfo":
        per_region("sfo")
    elif userinput.lower() == "pdx":
        per_region("pdx")
    elif userinput.lower() == "iad":
        per_region("iad")
    elif userinput.lower() == "gru":
        per_region("gru")
    elif userinput.lower() == "dub":
        per_region("dub")
    elif userinput.lower() == "nrt":
        per_region("nrt")
    elif userinput.lower() == "sin":
        per_region("sin")
    elif userinput.lower() == "syd":
        per_region("syd")
    elif userinput.lower() == "cmh":
        per_region("cmh")
    elif userinput.lower() == "yul":
        per_region("yul")
    elif userinput.lower() == "arn":
        per_region("arn")
    elif userinput.lower() == "fra":
        per_region("fra")
    elif userinput.lower() == "cdg":
        per_region("cdg")
    elif userinput.lower() == "lhr":
        per_region("lhr")
    elif userinput.lower() == "bah":
        per_region("bah")
    elif userinput.lower() == "hkg":
        per_region("hkg")
    elif userinput.lower() == "bom":
        per_region("bom")
    elif userinput.lower() == "icn":
        per_region("icn")
    elif userinput.lower() == "kix":
        per_region("kix")
    else:
        logging.info("Unsupport Region / Wrong Input")

if __name__ == "__main__":
        main()

