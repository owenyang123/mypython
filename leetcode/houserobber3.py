class Solution:


    def houseRobber3(self, root):
        # write your code here
        self.D = {}
        return max(self.dp(root, True), self.dp(root, False))

    def dp(self, node, robbed):
        if not node:
            return 0
        if (node, robbed) in self.D:
            return self.D[(node, robbed)]
        if robbed:
            self.D[(node, robbed)] = node.val + self.dp(node.left, False) + self.dp(node.right, False)
        else:
            self.D[(node, robbed)] = max(self.dp(node.left, True), self.dp(node.left, False)) + \
                                     max(self.dp(node.right, True), self.dp(node.right, False))
        return self.D[(node, robbed)]