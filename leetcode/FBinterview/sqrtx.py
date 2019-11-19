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


class Solution1:
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


class Solution2:
    # @param x : integer
    # @param n : integer
    # @param d : integer
    # @return an integer
    def pow(self, x, n, d):
        if x == 0 and n == 0:
            return 0
        if n == 0:
            return 1 % d
        c = x % d
        if x == 1:
            return 1 % d
        if n == 1:
            return c
        print n
        if n % 2 == 0:
            return (self.pow(c, n / 2, d) * self.pow(c, n / 2, d)) % d
        else:
            return (self.pow(c, n / 2, d) * self.pow(c, n / 2, d) * x) % d

k=Solution2()
print k.pow(71045970,41535484,64735492)

