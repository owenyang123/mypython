class Solution:
    # @param A : list of integers
    # @param B : integer
    # @return an integer
    def diffPossible(self, A, B):
        if len(A)<=1:
            return 0
        if A[-1]-A[0]<B:
            return 0
        i,j=0,len(A)-1
        while (i<j):
   
            if A[j]-A[i]==B:
                return 1
            if A[j]-A[i]>B and i==j-1:
                j-=1
                i=0
            elif  A[j]-A[i]>B:
                i+=1
            elif A[j]-A[i]<B:
                j-=1
                i=0
        return 0
k=Solution()
print k.diffPossible([1, 2, 2, 3, 4],0)