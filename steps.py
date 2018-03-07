import os
import random

step_num=int(input("input max steps:"))

l=[]
for x in range(1, step_num+2):
    l.append(x)
l[0]=1
l[1]=1
l[2]=2
l[3]=4
for x in range(4,step_num+1):
    t=l[x-1]+l[x-2]+l[x-3]
    l[x]=t
    print x
    print l,l.__len__()

