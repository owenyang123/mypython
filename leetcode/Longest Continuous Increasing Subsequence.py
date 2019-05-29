class Solution:
    """
    @param A: An array of Integer
    @return: an integer
    """

    def longestIncreasingContinuousSubsequence(self, A):
        if not A:
            return 0
        if len(A) == 1:
            return 1
        i = 0
        j = 1
        m1 = 0
        l1 = [0]
        while (j < len(A)):
            if A[j] > A[i]:
                m1 = m1 + 1
                j = j + 1
                i = i + 1
                if j == len(A):
                    l1.append(m1)
            else:
                l1.append(m1)
                m1 = 0
                i = i + 1
                j = j + 1
        i = 0
        j = 1
        m2 = 0
        l2 = [0]
        while (j < len(A)):
            if A[j] < A[i]:
                m2 = m2 + 1
                j = j + 1
                i = i + 1
                if j == len(A):
                    l2.append(m2)
            else:
                l2.append(m2)
                m2 = 0
                i = i + 1
                j = j + 1
        l1.sort()
        l2.sort()
        print l1, l2
        return max(l1[-1] + 1, l2[-1] + 1)

