class Solution:
    def searchInsert(self, A, target):
        if A == []:
            return 0
        A.append(target)
        A.sort()
        i = 0
        j = len(A) - 1
        mid = (i + j) / 2
        while (j - i > 0):
            if A[mid] == target:
                break
            elif A[mid] < target:
                i = mid
                mid = (i + j) / 2 + 1
            elif A[mid] > target:
                j = mid
                mid = (i + j) / 2
        if A[mid] == A[mid - 1] and mid != 0:
            mid = mid - 1
        return mid
