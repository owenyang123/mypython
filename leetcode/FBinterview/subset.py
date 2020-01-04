class Solution:
    """
    @param nums: A set of numbers
    @return: A list of lists
    """
    def subsets(self, nums):
        if not nums:
            return [[]]
        nums.sort()
        B=len(nums)
        combinations = []
        self.dfs(nums, 0, [], combinations, B)
        n = 0
        return combinations
    def dfs(self, nums, index, combination, combinations, B):
        combinations.append(list(combination))
        for i in range(index, len(nums)):
            combination.append(nums[i])
            self.dfs(nums, i +1, combination, combinations, B)
            combination.pop()