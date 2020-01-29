import copy
copy.
class Solution:
    # @param A : integer
    # @return a list of list of integers
    def solve(self, A):
        if A==0:return [[]]
        if A==1:return [[1]]
        if A==2:return [[1],[1,1]]
        l=[[1],[1,1]]
        temp=[]
        for i in range(2,A+1):
            temp=[1]+[0]*(i-1)+[1]
            for j in range(1,i):
                temp[j]=l[i-1][j-1]+l[i-1][j]
            l.append(temp)
            temp=[]
        return l[0:len(l)-1]

import copy
class Solution:
    def solve(self, A):
        if A==0:return []
        if A==1:return [[1]]
        l=[[1]]
        ret=[1]
        while True:
            for i in range(1, len(ret)):
                ret[i] = pre[i] + pre[i - 1]
            ret.append(1)
            pre = ret[:]
            temp=copy.deepcopy(ret)
            l.append(temp)
            if len(ret)>=A:
                break
        return l