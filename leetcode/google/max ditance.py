
class Solution1:
    # @param A : list of integers
    # @return a list of integers
    def subUnsort(self, A):
        flag=True
        if len(A)==1 or not A:
            return [-1]
        temp=[]
        for i in range(len(A)-1):
            if max(A[0:i+1])> min(A[i+1:]):
                flag=False
                temp.append(i)
        if flag:
            return -1
        else:
            return temp

x=Solution1()
print x.subUnsort([1, 3, 2, 4, 5])