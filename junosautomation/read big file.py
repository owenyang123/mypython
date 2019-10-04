import os
import re

with open("bgp summary", 'r') as f:
    for i in f:
        if re.search("Est",i):
            print i.split()





s=[]
print s[-1]