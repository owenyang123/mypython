l1=[3]*4+[5]*4


class Solution:

    def permuteUnique(self, nums):
        # write your code here
        if nums == None or len(nums) == 0:
            return [[]]
        nums = sorted(nums)
        visited = [0] * len(nums)

        res = []
        self.dfs(nums, [], res, visited)
        return res

    def dfs(self, nums, comb, res, visited):
        if len(comb) == len(nums):
            res.append(comb[:])

        for i in range(len(nums)):
            if visited[i] == 1 or (i != 0 and visited[i - 1] == 0 and nums[i] == nums[i - 1]):
                continue
            visited[i] = 1
            comb.append(nums[i])
            self.dfs(nums, comb, res, visited)
            comb.pop()
            visited[i] = 0
k=Solution()
x= k.permuteUnique(l1)

for i in x:
    print i[0]*10