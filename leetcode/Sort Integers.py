class Solution:
    """
    @param A: an integer array
    @return: nothing
    """
    def sortIntegers(self, A):
        if A==[] or A==None:
            return []
        A.sort()
        return A
k=Solution()
print k.sortIntegers([3,2,1,4,5])

print {0,1,2,3}.right