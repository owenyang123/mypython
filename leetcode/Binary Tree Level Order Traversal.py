class Solution:
    """
Definition of TreeNode:
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left, self.right = None, None
    """
    def levelOrder(self, root):
        # write your code here
        if not root: return []
        queue,result,last = [(root,1)],[],0
        while (queue):
            node,level = queue.pop(0)
            if level==last: result[-1].append(node.val)
            else: result.append([node.val])
            if node.left: queue.append((node.left,level+1))
            if node.right: queue.append((node.right,level+1))
            last = level
        return result