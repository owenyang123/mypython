import copy
def minimumTotal(self, triangle):
    n = len(triangle)

    # state: dp[i][j] 代表从 0, 0 走到 i, j 的最短路径值
    dp = [[0] * n, [0] * n]

    # initialize: 初始化起点
    dp[0][0] = triangle[0][0]

    # function: dp[i][j] = min(dp[i - 1][j - 1], dp[i - 1][j]) + triangle[i][j]
    # i, j 这个位置是从位置 i - 1, j 或者 i - 1, j - 1 走过来的
    for i in range(1, n):
        dp[i % 2][0] = dp[(i - 1) % 2][0] + triangle[i][0]
        dp[i % 2][i] = dp[(i - 1) % 2][i - 1] + triangle[i][i]
        for j in range(1, i):
            dp[i % 2][j] = min(dp[(i - 1) % 2][j], dp[(i - 1) % 2][j - 1]) + triangle[i][j]

    # answer: 最后一层的任意位置都可以是路径的终点
    return min(dp[(n - 1) % 2])