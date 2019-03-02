class Solution:
    def compareStrings(self, A, B):
        if B=="" or A==B:
            return True
        for i in B:
            if i not in A or A.count(i)<B.count(i):
                return False
        return True

k=Solution()
print k.compareStrings("AAA","AA")
