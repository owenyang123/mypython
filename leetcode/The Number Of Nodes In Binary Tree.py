class Solution:
    """
    @param root: the root of the binary tree
    @return: the number of nodes
    """
    result=[]
    def getAns(self, root):
        self.result=[]
        self.traverse(root)

    def traverse(self, root):
        if root is None:
            return
        self.results.append(root.val)
        self.traverse(root.left)
        self.traverse(root.right)

