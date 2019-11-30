
class Solution(object):
    # @param {NestedInteger[]} nestedList a list of NestedInteger Object
    # @return {int} an integer
    def depthSum(self, nestedList):
        self.sum = 0
        def dfs(nestedList,depth):
            for i in nestedList:
                if i.isInteger():
                    self.sum+=i.getInteger()*depth
                else:
                    dfs(i.getList(),depth+1)
        depth=1
        dfs(nestedList,1)
        return self.sum
