class Solution:
    # @param A : list of list of integers
    # @return the same list modified
    def rotate(self, A):
        rows,clos=len(A),len(A[0])
        B=[[0 for x in range(rows)] for y in range(clos)]
        for i in range(clos):
            for j in range(rows):
                B[i][j]=A[rows-1-j][i]
        return B
