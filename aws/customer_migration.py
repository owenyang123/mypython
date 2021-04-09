#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
'''
Customer_Migration
Version   Date         Author     Comments
1.00      2019-12-04   joaq@      First version only tested in NRT4 port migration
'''
import os,re

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#******************************************#
def print_help():
	print("""help/exit          Prints help, exits program.

get info           (1st step) Reads port information.
select             (2nd step) Autoport selection based on requirement inputs.
""")

#******************************************#			
def get_information():
	print("""DX Deployment is requesting API access to DXBI, which will automate this step.

For now, plese get the information from MaestroDB and save it in a file.
This file has to contain list of ports with DXCON/DXVIF owners from Maestro DB, like this:
| nrt4-vc-car-r1 | ge-0/0/0       | dxcon-zgh9mk7jhz2a  | 424677954942 | dx-con-ffiuum4d | available   | 225152034243 | 2016-10-26 05:56:32 | 2016-10-31 03:10:19 |
""")
	path = os.path.expanduser("~")
	file = input(f">>    Name of the file in '{path}/': ")
	ports = {}

	file = path + "/" + file

	if os.path.exists(file):
		f = open (file,'r')
		list_of_routers = []
		for line in f.readlines():
			port = "{}.{}.{}".format(line.split("| ")[1].split(".")[0].strip(),line.split(" | ")[1].strip(),line.split(" | ")[2].strip())
			if port not in ports:
				ports[port] = {}
				ports[port]["owners"] = []
				ports[port]["redundancy"] = []
				ports[port]["migration"] = []
			dxconowner = line.split(" | ")[3]
			dxvifowner = line.split(" | ")[6]
			if dxconowner not in ports[port]["owners"]:
				ports[port]["owners"].append(dxconowner)
			if dxvifowner not in ports[port]["owners"]:
				ports[port]["owners"].append(dxvifowner)

		for port in ports:
			router = port.split(".")[0][-2:]
			if router not in list_of_routers:
				list_of_routers.append(router)

		for port in ports:
			for owner in ports[port]["owners"]:
				for port_check in ports:
					if owner in ports[port_check]["owners"]:
						router = port_check.split(".")[0][-2:]
						if router not in ports[port]["redundancy"]:
							ports[port]["redundancy"].append(router)

		for port in ports:
			for router in list_of_routers:
				if router not in ports[port]["redundancy"]:
					ports[port]["migration"].append(router)
			print("\n{}:\nDXCON/DXVIF Owners: {}\nHas redundancy on: {}\nCan be migrated to: {}".format(port,ports[port]["owners"],ports[port]["redundancy"],ports[port]["migration"]))
	else:
		print(">> File {} not found.".format(file))

	return ports

#******************************************#
def select(ports_full):
	ports_mcm = {}

	min_vifcount = input(">>    Consider ports with at least VIF count [10]: ") or "10"
	min_vifcount = int(min_vifcount)
	
	migrate_from_routers = input(">>         Select source routers to migrate ports [r1,r2,r3,r4]: ") or "r1,r2,r3,r4"
	migrate_from_routers =  list(migrate_from_routers.split(","))
	migrate_to_routers = input(">>         Select destination routers to migrate ports [r5,r6]: ") or "r5,r6"
	migrate_to_routers = list (migrate_to_routers.split(","))
	
	migraton_type = input(">>    Migratin type (only option for now) [r[13] to r5, and, r[24] to r6][press Enter] ") or " "
	dest = {"r1":"r5","r2":"r6","r3":"r5","r4":"r6"}
	analysis = input(">>    Show analysis details (y/n)?[n]: ") or "n"
	if analysis == "y":
		show_analysis = True
	else:
		show_analysis = False
	
	for router in migrate_from_routers:
		print("\n\n\n\n\n****************************************************************************\n****************************************************************************\n**** Ports with more than {} VIF count, to migrate from {} to {}\n".format(min_vifcount,router,dest[router]))
		portcount = 0
		vifcount = 0
		for port in ports_full:
			if router in port.split(".")[0][-2:] and "ae" not in port.split(".")[1]:
				if ((router == "r1" and "r3" in ports_full[port]["migration"] and "r5" in ports_full[port]["migration"]) or (router == "r2" and "r4" in ports_full[port]["migration"] and "r6" in ports_full[port]["migration"])  or (router == "r3" and "r1" in ports_full[port]["migration"] and "r5" in ports_full[port]["migration"])  or (router == "r4" and "r2" in ports_full[port]["migration"] and "r6" in ports_full[port]["migration"])) and len(ports_full[port]["owners"]) > min_vifcount:
					if show_analysis:
						print("\n{}:\nDXCON/DXVIF Owners: {}\nHas redundancy on: {}\nCan be migrated to: {}".format(port,ports_full[port]["owners"],ports_full[port]["redundancy"],ports_full[port]["migration"]))
					else:
						print("{}\t{}".format(port.split(".")[0],port.split(".")[1]))
					vifcount += len(ports_full[port]["owners"])
					portcount += 1
		print("\n**** Total VIF count is {}, moving {} ports from {} to {}\n****************************************************************************\n****************************************************************************\n".format(vifcount,portcount,router,dest[router]))

	return ports_mcm


#******************************************#
def main():
	print(bcolors.HEADER)
	print(">> Customer Migration")
	print(bcolors.ENDC)
	ports_full = {}
	ports_mcm = {}
	print(bcolors.HEADER)
	command = input("\n(customer_migration)>> ")
	while command != "exit":
		commands = command.split()
		if len(commands) > 0:
			print(bcolors.ENDC)
			if command == "help":
				print_help()


			elif command == "get info":
				ports_full = get_information()

			elif command == "select":
				if ports_full == {}:
					print(">>    Please run 'get info' command first")
				else:
					ports_mcm = select(ports_full)

			else:
				print("Command not found, please try 'help'.\n")
			print(bcolors.HEADER)
			command = input("(customer_migration)>> ")
		else:
			command = input("(customer_migration)>> ")
	print(bcolors.ENDC)
if __name__ == '__main__':
	main()


