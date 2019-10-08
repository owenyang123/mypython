class Solution:
    """
    @param S: A list of integers
    @return: An integer
    """

    def triangleCount(self, S):
        if S is None or len(S) < 3:
            return 0

        S.sort()

        result = 0
        for right in range(len(S) - 1, 1, -1):
            result += self.two_sum(S, 0, right - 1, S[right])

        return result

    def two_sum(self, S, start, end, target):
        result = 0
        while start < end:
            if S[start] + S[end] <= target:
                start += 1
                continue

            result += end - start
            end -= 1

        return result