class Solution:
    """
    @param nums: a list of integer
    @param k: an integer
    @return: return an integer, denote the number of continuous subarrays whose sum equals to k
    """

    def subarraySumEqualsK(self, nums, k):
        presum = {0: 1}
        count = 0
        sum = 0
        for num in nums:
            sum += num
            if sum - k in presum:
                count += presum[sum - k]

            presum[sum] = presum.get(sum, 0) + 1

        return count