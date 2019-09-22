import copy
class Solution:
    def permute(self, nums):
        # write your code here
        def helper(res, nums, l):
            if (len(nums) == 0):
                if l not in res:
                    res.append(copy.deepcopy(l))
                return
            for i in range(len(nums)):
                temp = nums[i]
                l.append(temp)
                nums.pop(i)
                helper(res, nums, l)
                nums.insert(i, temp)
                l.pop()
        res = []
        helper(res, nums, [])
        return res
k=Solution()
print k.permute([1,2,2])




