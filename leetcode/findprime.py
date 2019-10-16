import math
import sys
import os
import re
def prime(n):
    if n<=1:
        return False
    if n==2 or n==3:
        return True
    if n%2==0:
        return False
    k=int(math.sqrt(n)+1)
    for i in range(3,k,2):
        if n%i==0:
            return False
    return True
def listprimes(n):
    l=[]
    for i in range(2,n+1):
        if not prime(i):
            continue
        l.append(i)
    return l

print prime(73)
print listprimes(101)

print  os.path.exists("D:/Python27/mypython2018/mypython/leetcode/findprime1.py")
