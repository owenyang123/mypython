import os, sys, time, datetime
from pprint import pprint  
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos import exception as EzErrors
from mail_message import Email_Alert

#Create backup directory 
current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
path = "/homes/jbrantley/work/lab_archives/%s" % current_timestamp 
router_path = "/config/juniper.conf.gz"

os.mkdir(path, 0755);

#define lab username and passwords 
user_name = 'labroot'
lab_password = 'lab123'

#Add routers or ips within '' seperated by comma 
system_host = ['d19-37.ultralab.juniper.net' ]

#add public ssh-key 
for hosts in system_host:
	dev = Device(host=hosts, user=user_name, password=lab_password)
	dev.open()
	with Config(dev, mode='private') as cu: 
	
		#Add public key to allow for copying config 
		set_cmd = "set system login user jbrantley class super-user authentication ssh-rsa \"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDE7RieImZfsMHuTk2nW+icMqHGUG7fb5lDc1wH+VzO1fkQZfu/tt/lvvi9RpT39jASAyaZGjpiJl7m+UtNcy+k46iE8QWVgJuQPEkHDz436lTe/P47ihdZxUl3jmzz1BnloB2Lpe8sn6US9KLB2jC3wq+zsIWGyp7thqCrraHENZ67qoIa5n9j8IVsJ/DsalKymfr9r/H40rsvy9VuaP7fowo3wjMOD0GoHf2gHef0ROH+ydtznGev8PKiR535exEwNT2H9Ts+SJfTZgx4jGfY5hCRpJiqBDSwDM/mKjJZoimI3umAJ7XPZbEQXr6lywESigKPiWWNMhJaEUEMeFp/KFt3cskTHadOB8L5RG7StHSzSkEXkm542ZplMCpNWVAOSVu+gjbXdxD+i7Uyfy+P1hM/8zSAcnehlyYyJbUqfp28xirGoIQ0tBo6ShALRs826k2M/4mRHe1kdNqmfsBwLUP9hfYHLOSWzA1jgn5K0f0MzFVgMvTJ0QECwj5YP4SR2nFfIlL4m3ZASeZFB4MisW/75XvmxQJErt5SxTHNHdw6P9NIyxdLQvSI0+r2gf7ZWabxu7kKSvkh9G4NCrZRkHsCD//v7DqY5PwYNriZiZhCCkzZ25YOJR7N8h7wGejNTnTsA88axKKg+YfkVwY0pY+ib2f3XAayu1nVP9QqEQ== jbrantley@juniper.net\""
		cu.load(set_cmd, format='set')
		cu.commit()
	
		#Move file over 
		os.system('scp "%s:%s" "%s/%s.conf.gz"' % (hosts, router_path, path, hosts))
		
		#Unzip file on share 
		os.system('gunzip "%s/%s.conf.gz"' % (path, hosts))
	
		#Clean public key off of box 
		set_cmd = 'delete system login user jbrantley'
		cu.load(set_cmd, format = 'set')
		cu.commit()	
	dev.close()  
Email_Alert()



