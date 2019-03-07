class Solution:

    def climbStairs(self, n):
        if n==None:
            return None
        if n==0:
            return 0
        if n==1 or n==2:
            return n
        dp=[0,1,2]
        for i in range(3,n+1):
            dp.append(dp[i-1]+dp[i-2])
        return dp[-1]
k=Solution()
print k.climbStairs(4)
