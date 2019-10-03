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

str = "The SraiSn in Spain123 456"
x = re.search(r"\bS\w+", str)
print x
print x.group()
print(x.span())