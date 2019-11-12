#-*- coding: utf-8 -*-
#!/usr/bin/python 
import paramiko
import threading

def ssh2(ip,username,passwd,cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip,22,username,passwd,timeout=5)
        for m in cmd:
            stdin, stdout, stderr = ssh.exec_command(m)
            out = stdout.readlines()
            for o in out:
                print o,
        print '%s\tOK\n'%(ip)
        ssh.close()
    except :
        print '%s\tError\n'%(ip)


if __name__=='__main__':
    cmd = ['cli','configure','run show version']
    username = "root"
    passwd = "Juniper"
    threads = []
    print "Begin......"
    for i in range(199,199):
        ip = '172.22.201.'+str(i)
        a=threading.Thread(target=ssh2,args=(ip,username,passwd,cmd))
        a.start()
