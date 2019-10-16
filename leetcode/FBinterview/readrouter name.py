import sys
import os
import re


def router_name(file):
    routerlist=[]
    with open(file, 'r') as hostnames:
        for line in hostnames.readlines():
            line.strip('\m')
            routerlist.append(line.split(" "))
    print routerlist
    return routerlist


if __name__ == "__main__":
    filename=raw_input("please input CORRECT file name with path:")
    if os.path.exists(filename):
        router_name(filename)
    else:
        print "please check the file path or the file does not exist "