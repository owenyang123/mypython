class Solution:
    # @param A : tuple of integers
    # @return a strings
    def largestNumber(self, A):
        # write your code here
        if A[0] == 0:
            return '0'
        return ''.join([str(v) for v in self.msort(A)])

    def msort(self, x):
        if len(x) == 1:
            return x
        mid = len(x) // 2
        a = x[:mid]
        b = x[mid:]
        a = self.msort(a)
        b = self.msort(b)
        res = self.merge(a, b)
        return res

    def merge(self, a, b):
        res = []
        i, j = 0, 0
        while i < len(a) and j < len(b):
            if str(a[i]) + str(b[j]) > str(b[j]) + str(a[i]):
                res.append(a[i])
                i += 1
            else:
                res.append(b[j])
                j += 1
        while i < len(a):
            res.append(a[i])
            i += 1
        while j < len(b):
            res.append(b[j])
            j += 1
        return res