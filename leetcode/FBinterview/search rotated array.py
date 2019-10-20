class Solution:
    # @param A : tuple of integers
    # @param B : integer
    # @return an integer
    def search(self, A, B):
        if not A:
            return -1

        start, end = 0, len(A) - 1
        while start + 1 < end:
            mid = (start + end) // 2
            if A[mid] >= A[start]:
                if A[start] <= B <= A[mid]:
                    end = mid
                else:
                    start = mid
            else:
                if A[mid] <= B <= A[end]:
                    start = mid
                else:
                    end = mid

        if A[start] == B:
            return start
        if A[end] == B:
            return end
        return -1