from jnpr.junos import Device
from multiprocessing import Process
import os
import csv

class automation_junos():
    def info_collecting(self,ipaddr,filename):
        dev = Device(host=ipaddr, user='labroot', password='lab123')
        dev.open()

        data = dev.facts
        with open(filename,"a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([data['hostname'] ,data['model']])
        dev.close()
        return


if __name__=='__main__':
    print('Parent process %s.' % os.getpid())
    filename="namemodel.csv"
    newdev=automation_junos()
    devlist=["10.85.174.196","10.85.174.190","10.85.174.78","10.85.174.66","10.85.174.69","10.85.174.57"]
    procs=[]
    for i in devlist:
        p=Process(target=newdev.info_collecting,args=(i,filename,))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()



