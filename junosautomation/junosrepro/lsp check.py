# 
#Psuedo Code 
#-> Open connection to device. 
#-> Run command: show mpls show mpls lsp | match detour
#		Expected output: ""Egress LSP: 800 sessions, 800 detours" - need to find a way to parse output, and verify that the detours = 800.  
#	-> If matching 800, then logon to transit device. "Egress LSP: 800 sessions, 800 detours"
#		-> login to the shell, "start shell pfe network fpcX"
#			-> port will be predetermined, so we will always be deactiving the same port. (show xfp list)
#			-> test xfp 1 laser off
#			-> wait 10 seconds
#			-> test xfp 1 laser on
#			-> go back to lsp detour match
#	-> If not matching, wait 30 seconds, and try again. 
#	-> Break mechanism to abort program. 
#-> End Program 

#Note: Requires netconf to be enabled. 

import sys
import time 
import datetime
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors
from lxml import etree


#Read file into device variable
#Input file should be CSV
input_file = raw_input('File to import devices from (needs to be a text file that seperates each host with a comma): ')
user = raw_input('Username: ')
passwd = getpass('Password: ')

#Open file specified by user, format it so that it can be used by the next if statement
device = []
for line in open(input_file,'r'):
	seperator = ','
	line = line.split(seperator)
	for value in line:
		device.append(value)

device = [x.strip('\n') for x in device]

#Login to each device. If it is up, perform the lsp check, then move on to the next one.  
#If a device is not up, exit and continue until list is completed.  
for item in device:
	dev=Device(user=user,host=item,password=passwd)
	dev.probe()
	print 'Opening connection to %s for user %s ...' % (item,user)
	
	if dev.probe() is True:
		dev.open()
		print '\nAll times are in UTC!\n\n'
		print datetime.datetime.utcnow()
		print 'Connection successful, starting script...'

		dev.timeout = 10*60
		
		#set variable that will be used to check 
		detour_good = "<detours>800</detours>"
		detour_check = 0
		count_checks = 0
		count_good = 3
				   
		while detour_check != detour_good:
			
			# Gather the info from the command 'show mpls lsp' and store it in variable mpls
			mpls = dev.rpc.get_mpls_lsp_information()
			mpls_data = etree.tostring(mpls)
			 
			#Need to parse through that data, and find '800 detours'
			#find index mpls_data.find('<detours>800</detours>')  This resulted in: 253450.  To get the exact length, counted the output: print mpls_data[253450:253472]
			# which prints <detours>800</detours> 
			
			#might want to do a double check, 5 minutes apart to verify lsps have recovered.  
			
			detour_check = mpls_data[253450:253472]
			if detour_check != detour_good:
				print datetime.datetime.utcnow()
				print detour_check
				print "Bummer, got to try again in 60 seconds."
				time.sleep(60)
			elif count_checks != count_good:
				while detour_check == detour_good and count_checks != count_good:
					print datetime.datetime.utcnow()
					print "Verifying LSPs are stable.  Waiting 5 minutes."  
					count_checks += 1
					time.sleep(300)
			else:
				break				
				
		print datetime.datetime.utcnow()		
		print detour_check
		print "MPLS Data matches!\n\n"
			 
		
	elif dev.probe() is False:
		print '%s is not reachable.  Skipping..' % (item)

print '\n\nExiting script.  Goodbye!'


	
	
	
		
		
	 
	 
	 
	 
	 

	
		
