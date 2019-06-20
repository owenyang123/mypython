import threading
import time

def show(arg,a):
    time.sleep(1)
    print('thread '+str(arg)+" running....")
    print a

if __name__ == '__main__':
    print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    for i in range(100):
        t = threading.Thread(target=show, args=(i,str(i)))
        t.start()
    t.join()
    print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
