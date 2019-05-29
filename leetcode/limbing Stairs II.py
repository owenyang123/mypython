class Solution:
    """
    @param n: An integer
    @return: An Integer
    """
    def climbStairs2(self, n):
        if not n:
            return 1
        l=[1,1,2,4]
        for i in range(4,n+1):
            print i
            l.append((l[i-3]+l[i-2]+l[i-1]))
        return l[n]
