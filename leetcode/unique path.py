class Solution:
    """
    @param m: positive integer (1 <= m <= 100)
    @param n: positive integer (1 <= n <= 100)
    @return: An integer
    """
    def uniquePaths(self, m, n):
         if m==1 or n==1 :
             return 1
         dp = [[0] * n for i in range(m)]
         print dp
         dp[0][0]=0
         for i in range(1, m):
             dp[i][0] = 1
         for i in range(1, n):
             dp[0][i] = 1
         for i in range(1, m):
             for j in range(1, n):
                 dp[i][j] = dp[i-1][j]+dp[i][j-1]
         return dp[-1][-1]
k=Solution()
print k.uniquePaths(20,20)