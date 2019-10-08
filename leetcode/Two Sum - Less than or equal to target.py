class Solution:

    def twoSum5(self, nums, target):
        if not nums:
            return 0
        ret = 0
        nums.sort()
        left, right = 0, len(nums)-1
        while left < right:
            tmp = nums[left] + nums[right]
            if tmp <= target:
                ret += right - left
                left += 1
            else:
                right -=1
        return ret


class Solution:
    """
    @param nums: an array of integer
    @param target: An integer
    @return: an integer
    """

    def twoSum2(self, nums, target):
        # write your code here
        n = len(nums)
        if n < 2:
            return 0

        nums.sort()

        res = 0
        l, r = 0, n - 1
        while l < r:
            if nums[l] + nums[r] <= target:
                l += 1
            else:
                res += r - l
                r -= 1

        return res


class Solution:
    """
    @param nums: an array of Integer
    @param target: an integer
    @return: [index1 + 1, index2 + 1] (index1 < index2)
    """

    def twoSum7(self, nums, target):
        # write your code here
        if not nums or target is None:
            return [0, 0]
        ndict = {}
        for i in range(len(nums)):
            if nums[i] + target in ndict:
                return [ndict[nums[i] + target] + 1, i + 1]
            if nums[i] - target in ndict:
                return [ndict[nums[i] - target] + 1, i + 1]
            ndict[nums[i]] = i

        return [0, 0]