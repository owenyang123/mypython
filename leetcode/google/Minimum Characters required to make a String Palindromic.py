class Solution:
    # @param A : string
    # @return an integer
    def solve(self, A):
        if self.helper1(A):
            return 0
        for i in range(len(A) - 1, 0, -1):
            if self.helper1(A[0:i]):
                return len(A)  - i
        return len(A) - 1

    def helper1(self, A):
        if len(A) == 1:
            return True
        l, r = 0, len(A) - 1
        while (l < r):
            if A[l] != A[r]:
                return False
            l += 1
            r -= 1
        return True

class Solution1:
    # @param A : string
    # @return a strings
    def longestPalindrome(self, A):
        if self.helper(A):
            return A
        temp = [1, 0, 1]
        for i in range(len(A) - 1):
            for j in range(i + 1, len(A)):
                if self.helper(A[i:j + 1]) and (len(A[i:j + 1]) > temp[0]):
                    temp[0]= len(A[i:j + 1])
                    temp[1]=i
                    temp[2]=j + 1

        return A[temp[1]:temp[2]]

    def helper(self, A):
        if A == A[::-1]:
            return True
        return False
k=Solution1()
print k.longestPalindrome("aaaabaaa")


x=[ 2, 0, 1, 2, 0, 3, 2, 2, 2, 1, 0, 0, 0, 1, 0, 0, 2, 2, 2, 3, 2, 3, 1, 2, 1, 2, 2, 3, 2, 3, 0, 3, 0, 2, 1, 2, 0, 0, 3, 2, 3, 0, 3, 0, 2, 3, 2, 2, 3, 1, 3, 3, 0, 3, 3, 0, 3, 3, 2, 0, 0, 0, 0, 1, 3, 0, 3, 1, 3, 1, 0, 2, 3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 2, 1, 0, 0, 0, 1, 0, 3, 2, 1, 0, 2, 3, 0, 2, 1, 1, 3, 2, 0, 1, 1, 3, 3, 0, 1, 2, 1, 2, 2, 3, 1, 1, 3, 0, 2, 2, 2, 2, 1, 0, 2, 2, 2, 1, 3, 1, 3, 1, 1, 0, 2, 2, 0, 2, 3, 0, 1, 2, 1, 1, 3, 0, 2, 3, 2, 3, 2, 0, 2, 2, 3, 2, 2, 0, 2, 1, 3, 0, 2, 0, 2, 1, 3, 1, 1, 0, 0, 3, 0, 1, 2, 2, 1, 2, 0, 1, 0, 0, 0, 1, 1, 0, 3, 2, 3, 0, 1, 3, 0, 0, 1, 0, 1, 0, 0, 0, 0, 3, 2, 2, 0, 0, 1, 2, 0, 3, 0, 3, 3, 3, 0, 3, 3, 1, 0, 1, 2, 1, 0, 0, 2, 3, 1, 1, 3, 2 ]

l=[1,2,3,4,5]
def pop123(A):
    A.pop()
pop123(l)
print l