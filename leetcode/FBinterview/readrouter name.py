import sys
import os
import re
import collections

def router_name(file):
    routerlist={}
    with open(file, 'r') as hostnames:
        for line in hostnames.readlines():
            temp=line.strip("\n").split("_")
            if temp[0] not in routerlist.keys():
                routerlist[temp[0]]={temp[1]:[temp[2]]}
            elif temp[1] not in routerlist[temp[0]].keys():
                routerlist[temp[0]][temp[1]]=[temp[2]]
            else:
                routerlist[temp[0]][temp[1]].append(temp[2])
    return routerlist

if __name__ == "__main__":
    filename=raw_input("please input CORRECT file name with path:")
    if os.path.exists(filename):
        k=router_name(filename)
        print k
        print k.keys()
        print k['sea'].keys()
    else:
        print "please check xxxx and try again "
        sys.exit()

words = re.findall(r'\w+', open('routername').read().lower().replace("_"," "))
print collections.Counter(words).most_common(3)

str.isalpha()
