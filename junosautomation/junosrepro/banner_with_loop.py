import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors

#Read file into device variable
input_file = raw_input('File to import devices from: ')
user = raw_input('Username: ')
passwd = getpass('Password: ')

#Open file specified by user
device = []
for line in open(input_file,'r'):
	seperator = ','
	line = line.split(seperator)
	for value in line:
		device.append(value)

device = [x.strip('\n') for x in device]
for item in device:
	dev=Device(user=user,host=item,password=passwd)
	dev.probe()
	print 'Opening connection to %s for user %s ...' % (item,user)
	
	if dev.probe() is False:
		print '%s is not reachable.  Skipping..' % (item)
	elif dev.probe() is True:
		dev.open()
		print 'Setting device parameter'

		dev.timeout = 10*60
		cu = Config(dev)

		print 'Setting banner message'
	
		set_cmd = 'set system login message "WARNING - THIS IS A PRIVATE SYSTEM"'
		cu.load(set_cmd, format='set')
		cu.pdiff()
		cu.commit_check
	
		print 'Check passed, committing changes...'

		cu.commit()

		print 'Exiting %s ' % (item)

		dev.close()
	#else:
	#	print 'No devices available...'

print 'All devices processed, exiting script.'
