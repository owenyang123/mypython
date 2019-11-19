import re
import os
n=1
l=[]
with open("piclog", 'r') as loglines:
    for line in loglines.readlines():
        print line
        if n%3==0:
            str123=""
            for i in range(len(line)):
                if line[i].isdigit():
                    str123+=line[i]
            l.append(int(str123))
        n+=1

for i in range(1,len(l)):
    if l[i]>l[i-1]:
        print "up "+str(l[i])
    else:
        print "down "+str(l[i])

print "max value is "+str(max(l))

