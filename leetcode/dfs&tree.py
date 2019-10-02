
"""
@param root: The root of binary tree.
@return: Preorder in ArrayList which contains node values.
"""


def preorderTraversal(self, root):
    self.results = []
    self.traverse(root)
    return self.results


def traverse(self, root):
    if root is None:
        return
    self.results.append(root.val)
    self.traverse(root.left)
    self.traverse(root.right)


def traverse(root, result):
    if not root:
        return
    traverse(root.left, result)
    result.append(root.val) # 注意访问根节点放到了遍历左子树的后面
    traverse(root.right, result)

def traverse(root, result):
    if not root:
        return
    traverse(root.left, result)
    traverse(root.right, result)
    result.append(root.val) # 注意访问根节点放到了最后

#level go through

class Solution:
    """
    @param root: A Tree
    @return: Level order a list of lists of integer
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

