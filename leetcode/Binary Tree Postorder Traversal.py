class Solution:
    """
    @param root: A Tree
    @return: Postorder in ArrayList which contains node values.
    """
    def postorderTraversal(self, root):
        # write your code here
        if root is None:
            return []
        mid = root.val
        left = self.postorderTraversal(root.left)
        right = self.postorderTraversal(root.right)
        return left + right + [mid]