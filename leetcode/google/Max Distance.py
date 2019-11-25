class Solution:
    # @param A : tuple of integers
    # @return an integer
    def maximumGap(self, A):
        if not A :return -1
        if len(A)==1:return 0
        flag=False
        l=[0]*len(A)
        for i in range(len(A)-1):
            if A[i]<A[i+1]:
                flag=True
            temp=0
            for j in range(i+1,len(A)):
                if A[j]>=A[i]:
                    temp=max(temp,j-i)
            l[i]=temp
        return max(l)