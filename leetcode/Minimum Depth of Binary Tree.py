class Solution:
    """
    @param root: The root of binary tree
    @return: An integer
    """
    def minDepth(self, root):
        # write your code here
        if root is None:
            return 0
        
        return self.helper(root)
        
        
    def helper(self, root):
        if root is None:
            return sys.maxint
            
        if root.left is None and root.right is None:
            return 1
        
        left = self.helper(root.left)
        right = self.helper(root.right)
        return min(left, right) + 1