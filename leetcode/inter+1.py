class Solution:
    # @param A : list of integers
    # @return a list of integers
    def plusOne(self, A):
        l=[]
        sum=0
        for i in range(len(A)):
            sum+=A[i]*(10**(len(A)-i-1))
        print sum
        sum+=1
        for i in str(sum):
            l.append(int(i))
        return l
k=Solution()
print k.plusOne([9,9])