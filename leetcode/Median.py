class Solution:
    """
    @param nums: A list of integers
    @return: An integer denotes the middle number of the array
    """
    def median(self, nums):
        nums.sort()
        if len(nums)%2==1:
            return nums[len(nums)/2]
        return nums[len(nums)/2-1]
