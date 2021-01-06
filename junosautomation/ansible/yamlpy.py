import yaml

with open("test.yaml", 'r') as stream:
    print(yaml.safe_load(stream))

import multiprocessing
from os import getpid

def worker(procnum):
    print('I am number %d in process %d' % (procnum, getpid()))
    return getpid()

if __name__ == '__main__':
    pool = multiprocessing.Pool(processes = 10)
    print(pool.map(worker, range(50)))
print "->".join(["1","2","3"])