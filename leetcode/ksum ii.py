class Solution:
    """
    @param: A: an integer array
    @param: k: a postive integer <= length(A)
    @param: target: an integer
    @return: A list of lists of integer
    """

    def kSumII(self, A, k, target):
        if not A or target is None:
            return []
        A.sort()
        self.res = []
        self.helper(A, 0, [], target)
        x1 = []
        for i in self.res:
            if len(i) == k:
                x1.append(i)

        return x1

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