import sys
class Solution:
    # @param A : list of integers
    # @return a list of integers
    def subUnsort(self, A):
        import copy
        backup_list=copy.deepcopy(A)
        backup_list.sort()
        if A==backup_list:return -1
        for i in range(len(A)-1):
            if A[i]>A[i+1]:
                for j in range(i+1,len(A)+1):
                    backup_list1=copy.deepcopy(A[i:j])
                    backup_list1.sort()
                    if j<=len(A) and ((A[0:i]+backup_list1+A[j:])==backup_list):
                        return [i,j-1]
        return -1

k=Solution()
print k.subUnsort([1,3,2,4,5])
l=sys.maxint