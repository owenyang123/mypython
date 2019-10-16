class Solution:
    # @param {TreeNode} root the root of binary tree
    # @return {int[][]} the vertical order traversal
    def verticalOrder(self, root):
        # Write your code here
        results = collections.defaultdict(list)
        import Queue
        queue = Queue.Queue()
        queue.put((root, 0))
        while not queue.empty():
            node, x = queue.get()
            if node:
                results[x].append(node.val)
                queue.put((node.left, x - 1))
                queue.put((node.right, x + 1))

        return [results[i] for i in sorted(results)]