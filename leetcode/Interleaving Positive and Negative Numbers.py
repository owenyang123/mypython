class Solution:
    """
    @param: A: An integer array.
    @return: nothing
    """

    def rerange(self, A):
        # write your code here
        left, right = 0, len(A) - 1

        while left < right:
            while left < right and A[left] < 0:
                left += 1
            while left < right and A[right] >= 0:
                right -= 1
            if left < right:
                A[right], A[left] = A[left], A[right]
                left += 1
                right -= 1
        if A[left] < 0:
            left += 1
        flag = 1
        if left < len(A) * 1.0 / 2:
            flag = 0
        print A, len(A), left, flag
        for i in range(len(A)):
            if i % 2 == flag:
                A[i], A[left] = A[left], A[i]
                left += 1
        return A