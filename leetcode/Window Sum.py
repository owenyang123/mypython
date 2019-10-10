class Solution:


    def winSum(self, nums, k):
        # write your code here
        n = len(nums)
        if n < k or k <= 0:
            return []
        tsum = [0] * (n - k + 1)
        for i in range(k):
            tsum[0] += nums[i]

        for i in range(1, n - k + 1):
            tsum[i] = tsum[i - 1] - nums[i - 1] + nums[i + k - 1]

        return tsum