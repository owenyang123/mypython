class Solution:
    # @param A : list of list of integers
    # @return an integer
    def uniquePathsWithObstacles(self, A):
        if not A or A[0][0]==1:
            return 0
        B=[[0 for x in range(len(A[0]))] for y in range(len(A))]
        B[0][0]=1
        for i in range(1,len(A)):
            if A[i][0]==1 or B[i-1][0]==0:
                B[i][0]=0
            else:
                B[i][0]=1
        for i in range(1,len(A[0])):
            if A[0][i]==1 or B[0][i-1]==0:
                B[0][i]=0
            else:
                B[0][i]=1
        print B
        for i in range(1, len(A)):
            for j in range(1, len(A[0])):
                if A[i][j] == 1:
                    B[i][j] = 0
                else:
                    B[i][j] = B[i - 1][j] + B[i][j - 1]
        return B

k=Solution()
l=[
  [0, 0, 1, 0, 1, 1, 1, 1],
  [0, 1, 0, 1, 0, 0, 1, 1],
  [0, 0, 1, 0, 0, 0, 0, 1],
]
print k.uniquePathsWithObstacles(l)

