dp = [[0 for i in range(500)] for j in range(500)]


mod = 1000000007
class Solution:


    def getAns(self, n, m, p):
        # Write your code here
        for i in range(500):
            for j in range(500):
                dp[i][j] = 0
        dp[0][0] = 1;
        for i in range(0, p + 1):
            for j in range(0, n + 1):
                # print i,j,dp[i][j]
                if (j < n):
                    dp[i + 1][j + 1] += dp[i][j] * (n - j);
                    dp[i + 1][j + 1] %= mod;
                if (j >= m):
                    dp[i + 1][j] += dp[i][j] * (j - m)
                    dp[i + 1][j] %= mod
        return dp[p][n]