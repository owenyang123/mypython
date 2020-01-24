class Solution:

    # find L/R first smaller than itself, increasing monotone stack
    def largestRectangleArea(self, height):
        height = [0] + height + [0]
        id_stack = []  # monotonic stack in the sense that height_ext[id_stack[:]] is monotonic
        area = 0
        for i, h in enumerate(height):
            # find the left / right first smaller than itself
            # montone increasing pop out all top element from stack if larger than new comer
            while id_stack and h <= height[id_stack[-1]]:  # kick out all greater than comming value h
                id = id_stack.pop()
                nh = height[id]
                w = (i - 1) - id_stack[-1] if len(id_stack) > 0 else i
                area = max(area, nh * w)
            id_stack.append(i)
        return area

    # similar problem
    # @param {boolean[][]} matrix, a list of lists of boolean
    # @return {int} an integer

    def maximalRectangle(self, matrix):
        if not matrix:
            return 0
        m, n = len(matrix), len(matrix[0])
        M = [[0 for j in range(n)] for i in range(m)]
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == 0:
                    M[i][j] = 0
                else:
                    M[i][j] = M[i - 1][j] + 1 if i >= 1 else 1
        max_area = 0
        print M
        for row in M:
            max_area = max(max_area, self.largestRectangleArea(row))
        return max_area





k=Solution()
l=[
  [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1],
  [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1],
  [1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0],
  [1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1],
  [1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1],
  [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1]
]

print k.maximalRectangle(l)