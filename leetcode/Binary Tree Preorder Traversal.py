class Solution:
    """
    @param root: A Tree
    @return: Preorder in ArrayList which contains node values.
    """

    def preorderTraversal(self, root):
        self.results = []
        self.traverse(root)
        return self.results

    def traverse(self, root):
        if root is None:
            return []
        self.results.append(root.val)
        self.traverse(root.left)
        self.traverse(root.right)

    def traverseinorder(root, result):
        if not root:
            return
        traverse(root.left, result)
        result.append(root.val)  # 注意访问根节点放到了遍历左子树的后面
        traverse(root.right, result)