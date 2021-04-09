question = input("Are you able to ssh to one of the devices[y/n] ?")
if (question.lower()=='y'):
    print(delete_request_commands.delete_request_software(devices)) # deletes puppet, chef commands. cannot commit if not deleted
else:
    print(bcolors.FAIL,"DNS may take a while to propogate. Wait 5 min and try again",bcolors.ENDC)
