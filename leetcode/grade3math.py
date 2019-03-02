class Solution:
    """
    @param a: A 32bit integer
    @param b: A 32bit integer
    @param n: A 32bit integer
    @return: An integer
    """

    def fastPower(self, a, b, n):
        # write your code here
        if a == 0:
            return 0
        if n == 0:
            return 1 % b
        if b==0:
            return 01
        if n===1:
            return a%b
        half = self.fastPower(a, b, n // 2)
        res = half * half
        if n % 2 == 1:
            res = res * (a % b)
        return res % b