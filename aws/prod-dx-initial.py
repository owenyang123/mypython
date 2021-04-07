#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from pexpect import pxssh
import getpass
import re

hostname_input = input ( "provide the list of devices (comma separated): " )
username = "root"
password = getpass.getpass ( prompt="Please Enter Root Password: " )
hostname_list = hostname_input.split ( ',' )

for hostname in hostname_list:
    try:
        s = pxssh.pxssh ()
        print ( "connecting to Device {}".format ( hostname ) )
        s.login ( hostname, username, password, original_prompt=r"[%>#$]")
        s.sendline ( 'cli' )  # run a command
        s.sendline ( 'show interface terse vme' )
        s.prompt ( timeout=1 )  # match the prompt
        cli = str ( s.before )
        print ( "Getting the vme and GW IPs" )
        vme_ip = re.search ( r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}', cli ).group ()
        s.sendline ( 'show dhcp client binding detail | match router' )
        s.prompt ( timeout=1 )
        cli2 = str ( s.before )
        cli2 = cli2[ 250: ]
        GW = re.search ( r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', cli2 ).group ()
        print ( "configuring Device {}".format ( hostname ) )
        s.sendline ( "edit" )
        s.sendline ( "delete interface vme unit 0 family inet dhcp" )
        s.sendline ( "set routing-options static route 0.0.0.0/0 next-hop {} no-readvertise".format ( GW ) )
        s.sendline ( "set interface vme unit 0 family inet address {}".format ( vme_ip ) )
        s.sendline ( "commit" )
        s.prompt ( timeout=5 )
        print ( "Configuration Sanity Check on {}".format ( hostname ) )
        cli3 = str ( s.before )
        commit = re.search ( r'commit complete', cli3 ).group ()
        if commit == "commit complete":
            print ( "Configuration Done Successfully" )
        else:
            print ( "Please Revise configuration" )
        s.sendline ( "exit" )
        s.sendline ( "exit" )
        s.logout ()
    except pxssh.ExceptionPxssh as e:
        print ( "SSH failed on login." )
        print ( e )
