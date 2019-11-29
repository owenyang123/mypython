class Solution:
    """
    @param A: a array
    @return: is it monotonous
    """

    def isMonotonic(self, A):
        # Write your code here.
        if not A:
            return False

        if len(A) == 1:
            return True

        status = -1  # 0:inc, 1: dec, -1: equal
        for i in range(1, len(A)):
            if A[i] > A[i - 1]:
                if status == 1:
                    return False
                if status == -1:
                    status = 0
            elif A[i] < A[i - 1]:
                if status == 0:
                    return False
                if status == -1:
                    status = 1

        return True

import copy
class Solution1:
    """
    @param A: a array
    @return: is it monotonous
    """
    def isMonotonic(self, A):
        l1=copy.deepcopy(A)
        l2=copy.deepcopy(A)
        l1.sort()
        l2.sort(reverse=True)
        if A==l1 or A==l2:
            return True
        return False