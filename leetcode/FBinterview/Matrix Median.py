class Solution:
    # @param A : list of list of integers
    # @return an integer
    def findMedian(self, A):
        l = []
        for i in A:
            l += i
        l.sort()
        return l[(len(l) / 2)]
