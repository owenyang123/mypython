class Solution:
    """
    @param m: positive integer (1 <= m <= 100)
    @param n: positive integer (1 <= n <= 100)
    @return: An integer
    """
    def uniquePathsWithObstacles(self,obstacleGrid):
         if obstacleGrid==[] or obstacleGrid==None or obstacleGrid[0][0]==1:
             return 0
         m=len(obstacleGrid)
         n=len(obstacleGrid[0])
         dp = [[0] * n for i in range(m)]
         dp[0][0]=0
         checkb=0
         for i in range(1, m):
             if obstacleGrid[i][0]==1:
                 checkb=1
             if checkb==1:
                dp[i][0]=0
             else:
                dp[i][0] = 1
         checkb = 0
         for i in range(1, n):
             if obstacleGrid[0][i] == 1:
                 checkb=1
             if checkb==1:
                 dp[0][i] = 0
             else:
                 dp[0][i] = 1
         print dp
         for i in range(1, m):
             for j in range(1, n):
                 if obstacleGrid[i][j]==1:
                     dp[i][j]=0
                 else:
                     dp[i][j] = dp[i-1][j]+dp[i][j-1]
         return dp
k=Solution()
print k.uniquePathsWithObstacles([[0,0,0],[0,1,0],[0,0,0]])