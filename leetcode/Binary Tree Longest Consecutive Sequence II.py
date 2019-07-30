"""
Definition of TreeNode:
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left, self.right = None, None
"""


class Solution:
    """
    @param root: the root of binary tree
    @return: the length of the longest consecutive sequence path
    """

    def longestConsecutive2(self, root):
        if not root:
            return None
        self.results = []
        self.traverse(root)
        self.results.sort()
        k = []
        temp = 1
        print self.results
        for i in range(len(self.results) - 1):
            if self.results[i + 1] == 1 + self.results[i]:
                temp += 1
                k.append(temp)
            else:
                pass
        k.sort(reverse=True)
        return k[0]

    def traverse(self, root):
        if root is None:
            return
        self.results.append(root.val)
        self.traverse(root.left)
        self.traverse(root.right)