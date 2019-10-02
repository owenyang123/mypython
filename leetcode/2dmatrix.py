import copy
class Solution:
    # @param A : integer
    # @return a list of list of integers
    def prettyPrint(self, A):
        k = 2 * A - 1
        m=k/2
        l1=[0]*k
        l=[]
        for i in range( k):
            temp=copy.deepcopy(l1)
            l.append(temp)
        for i in range(k):
            for j in range(k):
                if i==m and j==m:
                    l[i][j]=1
                else:
                    l[i][j]=1+max(abs(i-m),abs(j-m))
        return l

k=Solution()
print k.prettyPrint(10)