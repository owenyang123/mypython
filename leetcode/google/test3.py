class Solution:
    # @param A : list of list of integers
    # @return the same list modified
    def setZeroes(self, A):
        rowlist=[]
        collist=[]
        for i in range(len(A)):
            for j in range(len(A[0])):
                if A[i][j]==0:
                    rowlist.append(i)
                    collist.append(j)
        print(rowlist)
        print(collist)
        for i in range(len(A)):
            for j in range(len(A[0])):
                if (i in rowlist) or (j in collist):
                    A[i][j]=0
        return A

k=Solution()
l=[
  [0, 0],
  [1, 0]
]
print(k.setZeroes(l))