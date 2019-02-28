class Solution(object):
    def flatten(self, nestedList):
        ans = []
        if type(nestedList) == int:
            return [nestedList]
        def traverse(arr):
            for elem in arr:
                if type(elem) == int:
                    ans.append(elem)
                else:
                    traverse(elem)

        traverse(nestedList)
        return ans


k=[[1, 3, 5, 7],
    [10, 11, 16, 20],
    [23, 30, 34, 50]]
print len(k),len(k[1])