def threeSum(nums):
    l=[]
    if nums==[]:
        return []
    nums.sort()
    for i,j in enumerate(nums):
        left=i+1
        right=len(nums)-1
        while (left<right):
            s=j+nums[left]+nums[right]
            if s==0:
                if [j,nums[left],nums[right]] not in l:
                    l.append([j,nums[left],nums[right]])
                left=left+1
                right=right-1
            elif s<0:
                left=left+1
            elif s>0:
                right=right-1
    return l



class Solution:
    """
    @param numbers: Give an array numbers of n integer
    @return: Find all unique triplets in the array which gives the sum of zero.
    """

    def threeSum(self, numbers,target):
        if len(numbers) < 3:
            return []
        numbers.sort()
        l = []
        for i in range(len(numbers) - 2):
            self.twoSum6(numbers[i + 1:], target- numbers[i], l, numbers[i])

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
        return len(l)

k=Solution()
print k.threeSum([-1,0,1,2,-1,-4],5)


