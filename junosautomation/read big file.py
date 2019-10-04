import os
import re

with open("bgp summary", 'r') as f:
    f.read(1024)
    while True:
        buf = f.readlines()
        for i in buf:
            if re.search("Est",i):
                print i.split()
        break




s=[]
print s[-1]