"""
Definition of TreeNode:
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left, self.right = None, None
"""


class Solution:
    """
    @param root: the root of the binary tree
    @return: all root-to-leaf paths
    """

    def binaryTreePaths(self, root):
        if root is None:
            return []
        datalist = []
        path = ""
        self.binaryTreePaths2(root, path, datalist)
        return datalist

    def binaryTreePaths2(self, root, path, datalist):
        if root is None:
            return
        if path == "":
            path = str(root.val)
        else:
            path = path + "->" + str(root.val)
        if root.left is None and root.right is None:
            datalist.append(path)
            path = ""
            return
        self.binaryTreePaths2(root.left, path, datalist)
        self.binaryTreePaths2(root.right, path, datalist)
