#!/usr/bin/python

global router
global login
global pwd
global logTitle
global filename
global cmdFile
global session
global logFilePath
global emailFrom
global emailTo
router = "172.19.165.103" 
login = "lab" 
pwd = "herndon1"
logTitle = "Commands"
logExtnsn = '.log'
cmdFile = "CmdsToRun.txt"
logFilePath = "/home/deeptic/Desktop/SampleScrs/Python/TestScripts"
emailFrom = 'deeptic@juniper.net'
emailTo = 'deeptic@juniper.net'



def LoginRouter():
	import telnetlib
	global session
	session = telnetlib.Telnet(router)
	session.read_until("login:")
	session.write(login+"\n")
	session.read_until("Password:")
	session.write(pwd+"\n")


def RunCommands():
	for line in open(cmdFile):
		session.write(line)
	global output
	output=session.read_all()



def CreateLogfile():
	import datetime
	now = datetime.datetime.now() 
	logFile = "%s_%.2i-%.2i-%i_%.2i-%.2i-%.2i" % (logTitle,now.day,now.month,now.year,now.hour,now.minute,now.second)
	logFile = logFile + logExtnsn
	print output
	fp=open(logFile,"w")
	fp.write(output)
	fp.close()


def SendEmail():
	
	import smtplib
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText

	import os
	os.chdir(logFilePath)
	for files in os.listdir("."):
    		if files.endswith(logExtnsn):
        		filename = files
			#print filename


	msg = MIMEMultipart()
	fp = open(filename, 'rb')
	text = MIMEText(fp.read())
	fp.close()
	msg.attach(text)
	msg.attach(MIMEText(file(filename).read()))

	msg['Subject'] = 'Log File Captures' 
	msg['From'] = emailFrom
	msg['To'] = emailTo

	server = smtplib.SMTP("localhost")
	server.sendmail(emailFrom, [emailTo], msg.as_string())	
	server.quit()

	


	

LoginRouter()
RunCommands()
CreateLogfile()
SendEmail()



