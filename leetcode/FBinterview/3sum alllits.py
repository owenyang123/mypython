class Solution:
    """
    @param numbers: Give an array numbers of n integer
    @return: Find all unique triplets in the array which gives the sum of zero.
    """

    def threeSum(self, numbers):
        if len(numbers) < 3:
            return []
        numbers.sort()
        l = []
        for i in range(len(numbers) - 2):
            self.twoSum6(numbers[i + 1:], 0 - numbers[i], l, numbers[i])

        return l

    def twoSum6(self, nums, target, l, num):
        if len(nums) < 2:
            return l
        i = 0
        j = len(nums) - 1
        while (i < j):
            if nums[i] + nums[j] == target:
                if [num, nums[i], nums[j]] not in l:
                    l.append([num, nums[i], nums[j]])
                i += 1
                j -= 1
            elif nums[i] + nums[j] > target:
                j -= 1
            else:
                i += 1
        return l