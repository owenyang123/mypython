class Solution:
    # @param A : list of integers
    # @return a list of integers
    def wave(self, A):
        A.sort()
        result_list=[]
        lenth=len(A)
        for i in range(lenth/2):
            result_list.append(A[i*2+1])
            result_list.append(A[i*2])
        if lenth %2 ==1:
            result_list.append(A[-1])
        return result_list