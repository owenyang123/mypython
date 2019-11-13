#Import libraries needed 
import os, sys, time, datetime
from pprint import pprint  
from lxml import etree
from jnpr.junos import Device
import warnings 
from mail_message import Email_Alert

dev = Device(host = 'springfield.ultralab.juniper.net', user='labroot', password='lab123')  
dev.open()  
print datetime.datetime.utcnow()
#prompt for data to match
matching_condition = raw_input("What string do you want to match on? ") 
initial_condition = "null"
loop_counter = 1

#clear logs to start from a clean slate and not capture previous entries 
dev.rpc.clear_log(filename = 'messages') #will return output True - can be ignored 

#start log monitoring loop 
print "\n"
print datetime.datetime.utcnow()
print "Entering loop to search for issue"
while initial_condition != matching_condition:
	
	print datetime.datetime.utcnow()
	print "Round %s" % (loop_counter)
	
	#get log data 
	log_file_messages = dev.rpc.get_log(filename = 'messages')
	
	#convert output of messages to string 
	converted_log_file_messages = str((etree.tostring(log_file_messages)))
	if matching_condition in converted_log_file_messages:
		initial_condition = matching_condition
		print "Condition met, returning to beginning of loop which will end based on match"
		Email_Alert()
	else:
		time.sleep(10)
		loop_counter = loop_counter + 1 
dev.close()
print "Script completed"