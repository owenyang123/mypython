from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.utils.start_shell import StartShell
import json
import os
import csv
import threading
with open('2020-07-13.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        print row
with open('2020-07-13.csv', 'r') as file:
    for row in file.readlines():
        if row:print row.replace("\n","").replace("\r","").split(',')

x={'sea':{'core':["abc"]}}
l1=[["sea","ce","bcd"],["sea1","core","bcd"],["sea","ce","bcd1"],["sea3","ce","bcd1"],["sea","ce","aaabcd1"]]
for i in l1:
    if i[0] in x:
        if i[1] in x[i[0]]:
            x[i[0]][i[1]].append(i[2])
        else:
            x[i[0]][i[1]]=[i[2]]
    else:
        x[i[0]]={i[1]:[i[2]]}
print x

import collections


with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(10)