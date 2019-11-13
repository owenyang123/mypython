class Solution:
    # @param A : string
    # @param B : string
    # @return a strings
    def addBinary(self, A, B):
        a = self.b2d(A)
        b = self.b2d(B)
        return str(bin(a + b))[2:]

    def b2d(self, A):
        sum = 0
        for i in range(len(A)):
            if A[i] == "0":
                continue
            sum += 2 ** (len(A) - 1 - i)
        return sum
