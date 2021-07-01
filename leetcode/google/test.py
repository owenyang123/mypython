'''
#read big file

from functools import partial

def read_from_file(filename, block_size = 1024 * 8):
    with open(filename, "r") as fp:
        for chunk in iter(partial(fp.read, block_size), ""):
            yield chunk

def read_from_file(filename, block_size = 1024 * 8):
    with open(filename, "r") as fp:
        while chunk := fp.read(block_size):
            yield chunk

import collections
import re,copy


l=[1,2,3,4,6]

with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(10)


re_telephone = re.compile(r'^(\d{3})-(\d{3,8})$')
print re_telephone.match('010-12345').groups()
print re_telephone.match('010-8086').groups()
('010', '8086')

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
'''



class Solution:
    """
    @param s: an expression includes numbers, letters and brackets
    @return: a string
    """

    def expressionExpand(self, s):
        if not s: return ""
        if "[" not in s: return s
        for i in s:
            if i.isalnum():
                temp = self.helper(s)
                print temp[0],typotemp[1]
                return s[0:i] + self.expressionExpand(s[5:6])*int(i) + s[7:]

    def helper(self, s):
        b, e = 0, 0
        for i in range(len(s)):
            if s[i] == "[":
                b = i
                break
        for i in range(len(s) - 1, -1, -1):
            if s[i] == "]":
                e = i
                break
        return (b, i)

k=Solution()
print k.expressionExpand("abc3[a]")

class Solution:
    """
    @param s: an expression includes numbers, letters and brackets
    @return: a string
    """
    def expressionExpand(self, s):
        if not s:return ""
        if "[" not in s:return s
        temp=self.helper(s)
        return self.expressionExpand(s[0:temp[0]-temp[3]]+(s[temp[0]+1:temp[1]])*temp[2]+s[temp[1]+1:])
    def helper(self,s):
        b,e=0,0
        for i in range(len(s)):
            if s[i]=="[":
                b=i
            if s[i]=="]":
                e=i
                break
        temp,str1=b-1,""
        while(temp>=0):
            if s[temp].isdigit():
                str1+=s[temp]
                temp-=1
            else:break
        return (b,e,int(str1[::-1]),len(str1))

<<<<<<< HEAD
from jnpr.junos import Device
import threading
from lxml import etree
import datetime

list1=["erebus.ultralab.juniper.net","hypnos.ultralab.juniper.net","moros.ultralab.juniper.net","norfolk.ultralab.juniper.net","alcoholix.ultralab.juniper.net","antalya.ultralab.juniper.net","automatix.ultralab.juniper.net","beltway.ultralab.juniper.net","bethesda.ultralab.juniper.net","botanix.ultralab.juniper.net","dogmatix.ultralab.juniper.net","getafix.ultralab.juniper.net","idefix.ultralab.juniper.net","kratos.ultralab.juniper.net","pacifix.ultralab.juniper.net","photogenix.ultralab.juniper.net","rio.ultralab.juniper.net","matrix.ultralab.juniper.net","cacofonix.ultralab.juniper.net","asterix.ultralab.juniper.net","timex.ultralab.juniper.net","greece.ultralab.juniper.net","holland.ultralab.juniper.net","nyx.ultralab.juniper.net","atlantix.ultralab.juniper.net","obelix.ultralab.juniper.net","camaro.ultralab.juniper.net","mustang.ultralab.juniper.net"]
print(len(list1))
dict1={}
def listhw(str1):
    if not str1:return None
    global dict1
    try:
        dev = Device(host = str1, user='labroot', password='lab123')
        dev.open()
        x=dev.rpc.get_chassis_inventory()
        dev.close()
        head=etree.tostring(x).split("\n")
        temp=[str1]
        for i in head:
            if "description" in i:
                temp_str=i.replace("<"," ").replace(">"," ")
                if ("DPC" in temp_str or "MPC" in temp_str or "RE"in temp_str or "CB" in temp_str) and "PMB" not in temp_str:
                    if i[13]=="M" or i[13]=="D" or i[13]=="R":temp.append(i[13:-14])
        dict1[temp[0]]=list(set(temp[1:]))
    except:
        print(str1+" is unreachable")
        pass
    return
instance=[]
for i in list1:
    trd=threading.Thread(target=listhw,args=(i,))
    trd.start()
    instance.append(trd)
for thread in instance:
    thread.join()
temp=[]
for  i in dict1:
    temp.append([i]+sorted(dict1[i]))
temp.sort(key=lambda a:a[0])
for i in temp:
    print (i)
=======
>>>>>>> 512cb49dae98aca0d6726c1617974077117f6a35
