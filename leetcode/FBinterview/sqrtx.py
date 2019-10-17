class Solution:
    """
    @param: x: a double
    @return: the square root of x
    """

    def sqrt(self, x):
        if x >= 1:
            start, end = 1, x
        else:
            start, end = x, 1

        while end - start > 1e-10:
            mid = (start + end) / 2
            if mid * mid < x:
                start = mid
            else:
                end = mid

        return start


class Solution:
    """
    @param x: An integer
    @return: The sqrt of x
    """

    def sqrt(self, x):
        if x < 0:
            return None

        start, end = 0, x

        # find the last number that number^2 <= x
        while start + 1 < end:
            mid = (start + end) // 2
            if mid * mid <= x:
                start = mid
            else:
                end = mid

        if end * end <= x:
            return end

        return start