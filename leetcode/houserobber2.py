class Solution:
    """
    @param nums: numsn array of non-negative integers.
    @return: The maximum amount of money you can rob tonight
    """
    def houseRobber2(self, nums):
        if len(nums)==1:
            return nums[0]
        def houseRobber(nums):
            if nums == None or nums == []:
                return 0
            if len(nums) == 1:
                return nums[0]
            elif len(nums) == 2:
                return max(nums[0], nums[1])
            elif len(nums) == 3:
                return max(nums[0] + nums[2], nums[1])
            else:
                dp = [0] * len(nums)
                dp[0] = nums[0]
                dp[1] = max(nums[1], nums[0])
                dp[2] = max(nums[0] + nums[2], nums[1])
                for i in range(3, len(nums)):
                    dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
            return dp[-1]
        k=nums[::-1]
        return max(houseRobber(nums[0:-1]),houseRobber(k[0:-1]))