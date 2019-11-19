import threading
import time
list1=[x for x in range(100)]
def worker(n):
    """thread worker function"""
    print "ping  "+str(n)+"\n"
    time.sleep(0.1)
    print "ping "+str(n)+" is ok\n"
    return

threads = []
for i in range(len(list1)):
    t = threading.Thread(target=worker,args=(i,))
    threads.append(t)
    t.start()