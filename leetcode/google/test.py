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

