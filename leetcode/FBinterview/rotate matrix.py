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

def maxfactor(a,b):
    if a <= 0 or b <= 0:
        return None
    if a>b :
        return maxfactor(b,a)
    if b%a==0:
        return a
    else:
        return maxfactor(b%a, a)

alst=[1,2,3,4,5,6]
print list(filter(lambda  x:x%2==1,alst))