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


class Solution:
    """
    @param A: an integer array
    @param target: An integer
    @param k: An integer
    @return: an integer array
    """
    def kClosestNumbers(self, A, target, k):
        l=[]
        for i in A:
            l.append([abs(i-target),i])
        l.sort(key=lambda l:l[0])
        l1=[]
        for i in range(k):
            l1.append(l[i][1])
        return l1
