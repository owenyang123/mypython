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

class Solution(object):
    def maxProfit(self, prices):
        if len(prices)<=1 or not prices:return 0
        dp=[prices[0]]+[0]*(len(prices)-1)
        temp=prices[0]
        for i in range(len(prices)):
            temp=min(temp,prices[i])
            dp[i]=prices[i]-temp
        return max(dp) if max(dp)>0 else 0

class Solution:
    def maxAncestorDiff(self, root):
        self.ans = 0
        def dfs(root, l, h):
            if not root:
                self.ans = max(self.ans, h-l)
                return
            l = min(l,root.val)
            h = max(h,root.val)
            dfs(root.left, l, h)
            dfs(root.right, l, h)
        dfs(root, root.val, root.val)
        return self.ans