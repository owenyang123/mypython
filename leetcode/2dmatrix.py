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
print k.prettyPrint(5)


class Solution1:
    # @param A : list of list of integers
    # @return the same list modified
    def rotate(self, A):
        rows,clos=len(A),len(A[0])
        B=[[0 for x in range(rows)] for y in range(clos)]
        for i in range(clos):
            for j in range(rows):
                B[i][j]=A[rows-1-j][i]
        return B


k1=Solution1()
print k1.rotate([[1,2,7],[3, 4,8],[5,6,9]])
