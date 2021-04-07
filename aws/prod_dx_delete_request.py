#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import delete_request_commands
devices = input("enter list of devices separated by commas (bah52-vc-edg-r201,bah52-vc-edg-r202):")

devices = devices.split(',')

question = input("Are you able to ssh to one of the devices[y/n] ?")
if (question.lower()=='y'):
    print(delete_request_commands.delete_request_software(devices)) # deletes puppet, chef commands. cannot commit if not deleted
else:
    print("DNS may take a while to propogate. Wait 5 min and try again")
