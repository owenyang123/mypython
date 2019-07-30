class Solution:
    """
    @param num: Given the candidate numbers
    @param target: Given the target number
    @return: All the combinations that sum to target
    """

    def combinationSum2(self, num, target):
        # write your code here
        if not num or target is None:
            return []
        num.sort()
        self.res = []
        self.helper(num, 0, [], target)
        return self.res

    def helper(self, num, start, last_list, target):
        if target == 0:
            self.res.append(last_list[:])
            return
        if start >= len(num):
            return
        for i in range(start, len(num)):
            if (i != start) and (num[i] == num[i - 1]):
                continue
            if target - num[i] < 0:
                break
            last_list.append(num[i])
            self.helper(num, i + 1, last_list, target - num[i])
            last_list.pop()
        return