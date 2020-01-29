import collections
class Solution:
    # @param A : tuple of integers
    # @return an integer
    def repeatedNumber(self, A):
        if not A:
            return -1
        if len(A)<=2:
            return A[0]
        num=len(A)/3
        counterlist=collections.Counter(A)
        for i in counterlist:
            if counterlist[i]>num:
                return i
        return -1
print Solution().repeatedNumber([1,2,3,1,1])