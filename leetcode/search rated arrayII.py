class Solution:
    """
    @param A: an integer ratated sorted array and duplicates are allowed
    @param target: An integer
    @return: a boolean
    """
    def search(self, A, target):
        if not A:
            return False
        A.sort()
        left=0
        right=len(A)-1
        mid=(left+right)/2
        while (left-1<right):
            if A[mid]==target:
                return True
            if A[mid]>target:
                right=mid
                mid=(left+right)/2
            elif A[mid]<target:
                left=mid
                mid = (left + right) / 2
        if A[left]!=target and A[right]!=target:
            return Fasle:
        else:
        return True


