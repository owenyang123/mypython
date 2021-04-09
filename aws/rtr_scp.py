#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
import pexpect
import getpass
from pathlib import Path

list_of_devices = input ( "provide the list of devices (comma separated): " )
rebased_or_not = input ( "Are the devices rebased - Need Amazon Authentication - (yes/no)? " )
home = str ( Path.home () )
devices = list_of_devices.split ( ',' )
configfiles = [ ]
for i in devices:
    i = i+".cfg"
    configfiles.append ( i )
def NOT_Rebased():
    root_password = getpass.getpass ( prompt="Please Enter ROOT Password: " )
    for router in devices:
         spawn_command = 'scp -r '+ home +'/config/scripts '+'root@'+ router +':/config'
         print ( "Transferring Slax Scripts and BGP license to {} ".format(router))
         print ( spawn_command )
         child = pexpect.spawn ( spawn_command )
         cli_output = child.expect ( [ 'connecting', 'Password', 'password' ] )
         if cli_output == 0:
             child.sendline ( 'yes' )
         if cli_output == 1:
            child.sendline ( root_password )
            child.expect ( pexpect.EOF )
         print (" . . . Done")

    # Config Files transfer
    for i, router in enumerate ( devices ):
        for j, configfile in enumerate ( configfiles ):
            if i == j:
                spawn_command_config_file = 'scp '+ home +'/config/'+ configfile +' root@'+router+':/var/root'
                print ("Transferring Config files to {} ".format(router))
                print ( spawn_command_config_file)
                child = pexpect.spawn ( spawn_command_config_file )
                cli_output = child.expect ( [ 'connecting', 'password:', 'Password' ] )
                if cli_output == 0:
                    child.sendline ( 'yes' )
                if cli_output == 1:
                    child.sendline ( root_password )
                if cli_output == 2:
                    child.sendline ( root_password )
                    child.expect ( pexpect.EOF )
                print ( " . . . Done" )

def Rebased():
    # Config Files transfer
    Amazon_username = getpass.getuser()
    Amazon_password = getpass.getpass ( prompt="Please Enter domain Password: " )
    print("cfg files will be in /tmp folder. Use load override /tmp/device.cfg then commit")
    for i, router in enumerate ( devices ):
        for j, configfile in enumerate ( configfiles ):
            if i == j:
                spawn_command_config_file = 'scp '+ home +'/config/'+ configfile +' ' + Amazon_username + '@'+router+':/tmp/'
                print ( "Transferring Config files to {} ".format ( router ) )
                child = pexpect.spawn ( spawn_command_config_file )
                cli_output = child.expect ( [ 'connecting', 'password:', 'Password' ] )
                if cli_output == 0:
                    child.sendline ( 'yes' )
                if cli_output == 1:
                    child.sendline ( Amazon_password )
                if cli_output == 2:
                    child.sendline ( Amazon_password )
                    child.expect ( pexpect.EOF )
                print ( " . . . Done" )

if rebased_or_not == 'yes':
    Rebased()
if rebased_or_not == 'no':
    NOT_Rebased()
