class Solution:
    # @param A : tuple of integers
    # @return an integer
    def repeatedNumber(self, A):
        if not A:
            return -1
        if len(A)<=2:
            return A[0]
        B=list(A)
        B.sort()
        integer_dict={}
        lenth=len(B)
        target=lenth/3
        for i in B:
            if i in integer_dict.keys():
                integer_dict[i]+=1
                if integer_dict[i]>target:
                    return i
            else:
                integer_dict[i]=1
        return -1