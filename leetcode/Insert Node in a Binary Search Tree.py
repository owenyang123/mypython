class Solution:
    """
    @param: root: The root of the binary search tree.
    @param: node: insert this node into the binary search tree
    @return: The root of the new binary search tree.
    """

    def insertNode(self, root, node):
        # write your code here
        nd = root
        if nd is None:
            return node

        notDone = True
        while notDone:
            if node.val >= nd.val:
                if nd.right:
                    nd = nd.right
                else:
                    nd.right = node
                    notDone = False

            else:
                if nd.left:
                    nd = nd.left
                else:
                    nd.left = node
                    notDone = False

        return root