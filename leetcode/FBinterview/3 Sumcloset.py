class Solution:
    # @param A : list of integers
    # @param B : integer
    # @return an integer
    def threeSumClosest(self, nums, target):
# write your code here


if len(nums) < 3 or target is None:
    return 0

nums.sort()

n = len(nums)
min_diff = sys.maxsize
res = None

for i in range(n):
    if i > 0 and nums[i] == nums[i - 1]:
        continue

    l, r = i + 1, n - 1

    while l < r:
        s = nums[i] + nums[l] + nums[r]
        if s == target:
            return s

        if s < target:
            l += 1
        else:
            r -= 1

        if abs(target - s) < min_diff:
            min_diff = abs(target - s)
            res = s

return res