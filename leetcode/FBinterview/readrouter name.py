import sys
import os
import re
import collections

def router_name(file):
    routerlist={}
    with open(file, 'r') as hostnames:
        for line in hostnames.readlines():
            temp=line.split(" ")
            if temp[0] not in routerlist.keys():
                routerlist[temp[0]]=[temp[1:]]
            else:
                routerlist[temp[0]].append(temp[1:])
    return routerlist


if __name__ == "__main__":
    filename=raw_input("please input CORRECT file name with path:")
    if os.path.exists(filename):
        k=router_name(filename)
        for i in k.keys():
            for j in k[i]:
                if j[0]=="core":
                    print i,j[-1].strip("/n")
    else:
        print "please check the file path or the file does not exist "

words = re.findall(r'\w+', open('ospfdb').read().lower())
print collections.Counter(words).most_common(20)