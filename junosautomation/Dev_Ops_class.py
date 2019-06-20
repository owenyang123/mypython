from jnpr.junos import Device
import sys
import threading
import time


class JNPRdevops:
    def healthcheck(self, A,users,password):
        if not A:
            print "not valid"
        dev = Device(host=A, user=users, passwd=password)
        try:
            dev.open()
        except Exception as err:
            print err
            sys.exit(1)
        print dev.facts
        dev.close()


def show(arg,a):
    time.sleep(1)
    print('thread '+str(arg)+" running....")
    print a

if __name__ == "__main__":
    print ""
    k=JNPRdevops()
    l1=["10.85.173.179"]
    print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    for i in l1:
        t = threading.Thread(target=k.healthcheck, args=(i,"labroot","lab123",))
        t.start()
    t.join()
    print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
