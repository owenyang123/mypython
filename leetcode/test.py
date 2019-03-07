class Solution:
    """
    @param grid: a list of lists of integers
    @return: An integer, minimizes the sum of all numbers along its path
    """

    def minPathSum(self, grid):
        # write your code here
        row = len(grid)
        col = len(grid[0])
        dp = [[1] * col for i in range(row)]

        dp[0][0] = grid[0][0]
        for i in range(1, row):
            dp[i][0] = dp[i - 1][0] + grid[i][0]
        print dp
        for j in range(1, col):
            dp[0][j] = dp[0][j - 1] + grid[0][j]
        print dp
        for i in range(1, row):
            for j in range(1, col):
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1]) + grid[i][j]
        print dp
        print grid
        return dp[row - 1][col - 1]
k=Solution()

print k.minPathSum([[1,3,1],[1,5,1],[4,2,1]])