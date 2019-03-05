class Solution:
    def maxSubArray(self, nums):
        if max(nums)<=0:
            return [max(nums)]
        if min(nums)>0:
            return nums
        left=0
        right=0
        for i in range(len(nums)):
            if nums[i]>0:
                left=i
                break
        for i in range(len(nums)):
            if nums[-1-i]>0
                right=len(nums)-1-i
                break
        if left==right:
            return [nums[left]]
        while (left<right):
            if nums[left]+nums[left]


