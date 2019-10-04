import os
import re
sum=0
with open("bgp summary", 'r') as f:
    for i in f:
        if re.search("Est",i):
            print [i.split()[0],i.split()[-1]]
            sum=sum+1
print sum

str = "The SraiSn in Spain123 456"
x = re.search(r"\bS\w+", str)
print x
print x.group()
print(x.span())