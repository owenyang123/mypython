class Solution:
    # @param A : tuple of integers
    # @return an integer
    def lis(self, A):
        if not A:return None
        if len(A)==1:return 1
        default_list=[1]*len(A)
        for i in range(1,len(A)):
            temp = 0
            if self.helper(A,i)!=-1:
                for j in self.helper(A,i):
                    temp=max(temp,default_list[j])
                default_list[i]+=temp
        return default_list
    def helper(self,A,n):
        if n==1 and A[0]>A[n]: return -1
        temp_l=[]
        if A[n]<=min(A[0:n]):return -1
        for i in range(0,n):
            if A[i]<A[n]:


                temp_l.append(i)
        if temp_l==[]:
            return -1
        return temp_l

k=Solution()
print k.lis([1,3,5])