#!/usr/bin/python
#jbratley@juniper.net

def Email_Alert():

	# Import smtplib for the actual sending function
	import smtplib

	# Define email sender and receiver 
	email_source = 'jbrantley@juniper.net'
	email_destination = 'jbrantley@juniper.net'
	
	# Create message
	from email.mime.multipart import MIMEMultipart
	msg = MIMEMultipart()
			
	# Craft email
	msg['Subject'] = 'Backup Completed.'
	msg['From'] = email_source
	msg['To'] = email_destination
	
	# Send the message 
	email_server = smtplib.SMTP('localhost')
	email_server.sendmail(email_source, [email_destination], msg.as_string())
	email_server.quit()
	return;