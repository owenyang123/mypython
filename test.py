class Solution(object):
    def rob(self, nums):
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
            return  "".join(dp)

k="123"
s="weiqwieqw"
print "".join([1,2,3])
