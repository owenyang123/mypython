import os
import re

with open("bgp summary", 'r') as f:
    for i in f:
        if re.search("Est",i):
            print i.split()


str = "The SraiSn in Spain123 456"
x = re.search(r"\bS\w+", str)
print x
print x.group()
print(x.span())