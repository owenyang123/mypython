class Solution:
    """
    @param nums: A list of integers
    @return: A integer indicate the sum of max subarray
    """
    def maxSubArray(self, nums):
        if not nums:
            return []
        if len(nums)==1:
            return nums[0]
        s=1
        for i in nums:
            if i<0:
                s=0
        if s==1:
            return sum(nums)
        else:
            l2=[nums[0]]
            if nums[0]>=0:
                l1=[0]
                temp=0
            else:
                l1=[nums[0]]
                temp=nums[0]
            temp2=nums[0]
            l3=[nums[0]]
            for i in range(1,len(nums)):
                temp=min(temp,(sum(nums[0:i])+nums[i]))
                l1.append(temp)
                l3.append(sum(nums[0:i+1])-l1[i-1])
            l3.sort()
            return l3[-1]
######################################

class Solution1:
    """
    @param nums: A list of integers
    @return: A integer indicate the sum of max subarray
    """

    def maxSubArray(self, nums):
        min_sum, max_sum = 0, -sys.maxsize
        prefix_sum = 0

        for num in nums:
            prefix_sum += num
            max_sum = max(max_sum, prefix_sum - min_sum)
            min_sum = min(min_sum, prefix_sum)

        return max_sum
