import sys
class Solution:
    def maxset(self, A):
        n=len(A)
        if n==1:
            return A[0]
        min_prefix_sum=0
        max_sum=-sys.maxsize
        prefix_sum=0
        l=[]
        for num in A:
            prefix_sum+=num
            if max_sum<(prefix_sum-min_prefix_sum):
                l.append(num)
            max_sum=max(max_sum,prefix_sum-min_prefix_sum)
            min_prefix_sum=min(min_prefix_sum,prefix_sum)
        if sum(l)<0:
            return []
        else:
            return l

k=Solution()
print k.maxset([ -1, -1, -1, -1, -1 ])

kk