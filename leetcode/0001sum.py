class Solution:
    def twoSum(self, nums, target):
        lookup = {}
        for i, v in enumerate(nums):
            lookup[v] = i
        for i in range(len(nums)):
            if target - nums[i] in lookup and lookup[target - nums[i]] != i:
                return [i, lookup[target - nums[i]]]