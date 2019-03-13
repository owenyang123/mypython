class Solution:

    def minPathSum(self, grid):
        if grid==[] or grid[0]==[]:
            return []
        m=len(grid)
        n=len(grid[0])
        dp=[[0]*n for i in range(m)]
        dp[0][0]=grid[0][0]
        for i in range(1,m):
            dp[i][0]=dp[i-1][0]+grid[i][0]
        for i in range(1,n):
            dp[0][i]=dp[0][i-1]+grid[0][i]
        return dp

k=Solution()
print k.minPathSum([[1,3,1],[1,5,1],[4,2,1],[5,6,7]])
