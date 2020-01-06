list1 = ["a","e","i","o","u","A","E","I","O","U"]


class Solution:
    # @param A : string
    # @return an integer
    def solve(self, A):
        l = []
        for i in range(len(A)):
            if A[i] in list1:
                for j in range(len(A[i:])):
                    if A[i:j] not in l:
                        l.append(A[i:j])
        return l

k=Solution()
print k.solve("AzZGBauYu")

