######################################################################
##Script is used to add config and perform rollback loop from remote##
##	-server continuously                                            ## 
##Criteria of server running the program: python/PyEZ installed     ##
##	for example svl-jtac-lnx01 can be used for this                 ##
##Criteria of lab device: netconf over ssh                          ##
######################################################################
## V1.0 - Initial Draft                                             ##
## V1.1 - Added version control, Added print statements             ##
##		  Added variable rollbackloop_timer		       				##
##Comments or Improvements: write to gowtham@juniper.net            ##
######################################################################

#import required functions
import time
import datetime
from pprint import pprint
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

#Function to add config and perform rollback loop continuously.
def config_set_roll_loop(host_name, user_name, password, rollbackloop_timer):#function definition
	try:	                                                                 #try/except block for exception handling
		print "Started executing the script"
		counter = 0
		#Start config mode
		config_set = '''                                                     
		set interfaces xe-0/0/30 enable
		set interfaces xe-0/0/31 enable
		set interfaces xe-0/0/32 enable
		'''                                                                  #Paste config replacing above 3 lines in set format
		dev = Device(host=host_name, user=user_name, password=password)
		dev.open()
		dev.timeout = 300
		config = Config(dev)
		config.load(config_set, format="set", merge=True)
		config.commit(timeout=60)
		time.sleep(60)
		print "Committed the config, rollback loop will be initiated"
		while True:
			config.rollback(1)
			config.commit(timeout=60)
			counter += 1
			print "Round %s" % counter
			time.sleep(rollbackloop_timer)
		dev.close()
	except KeyboardInterrupt:
		print "\nProgram terminated from key board"
	except:
		print "\nError occurred while testing, validate parameters entered"
		
#main program		
if __name__ == "__main__":
	try:
		host_name = "172.22.146.65"                                              #Enter host name
		user_name = "root"                                                       #Enter user name
		password = "Juniper"                                                     #Enter password
		rollbackloop_timer = 60                                                  #Enter time in seconds between config rollbacks
		config_set_roll_loop(host_name, user_name, password, rollbackloop_timer)	
	except SyntaxError:
		print "syntax error"
	except:
		print "Error occurred while executing, check parameters provided"