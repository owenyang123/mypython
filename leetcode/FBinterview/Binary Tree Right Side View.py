class Solution:
    """
    @param root: the root of the given tree
    @return: the values of the nodes you can see ordered from top to bottom
    """
    def rightSideView(self, root):
        if not root: return []
        queue,result,last = [(root,1)],[],0
        while (queue):
            node,level = queue.pop(0)
            if level==last: result[-1].append(node.val)
            else: result.append([node.val])
            if node.left: queue.append((node.left,level+1))
            if node.right: queue.append((node.right,level+1))
            last = level
        return [i[-1] for i in result]
