class Solution:
    """
    @param grid: a boolean 2D matrix
    @return: an integer
    """

    def numIslands(self, grid):
        # write your code here
        if not grid or not grid[0]:
            return 0
        ret = 0
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1:
                    ret += 1
                    self.removeIsland(grid, i, j)
        return ret

    def removeIsland(self, grid, i, j):
        grid[i][j] = 0
        if i > 0 and grid[i - 1][j] == 1:
            self.removeIsland(grid, i - 1, j)
        if i < len(grid) - 1 and grid[i + 1][j] == 1:
            self.removeIsland(grid, i + 1, j)
        if j > 0 and grid[i][j - 1] == 1:
            self.removeIsland(grid, i, j - 1)
        if j < len(grid[0]) - 1 and grid[i][j + 1] == 1:
            self.removeIsland(grid, i, j + 1)
count=0
class Solution1:
    """
    @param grid: a 2D array
    @return: the maximum area of an island in the given 2D array
    """

    def maxAreaOfIsland(self, grid):
        # write your code here
        if not grid or not grid[0]:
            return 0
        ret = 0
        temp=0
        global count
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1:
                    ret += 1
                    count=0
                    self.removeIsland(grid, i, j)
                    temp=max(temp,count)

        return temp

    def removeIsland(self, grid, i, j):
        global count
        count+=1
        grid[i][j] = 0
        if i > 0 and grid[i - 1][j] == 1:
            self.removeIsland(grid, i - 1, j)
        if i < len(grid) - 1 and grid[i + 1][j] == 1:
            self.removeIsland(grid, i + 1, j)
        if j > 0 and grid[i][j - 1] == 1:
            self.removeIsland(grid, i, j - 1)
        if j < len(grid[0]) - 1 and grid[i][j + 1] == 1:
            self.removeIsland(grid, i, j + 1)