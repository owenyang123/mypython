class Solution:
    """
    @param A: an integer sorted array
    @param target: an integer to be inserted
    @return: a list of length 2, [index1, index2]
    """
    def searchRange(self, A, target):
        if not A or target not in A:
            return [-1,-1]
        l=[]
        for i in range(len(A)):
            if A[i]==target:
                l.append(i)
                break
            else:
                pass
        if l[0]==len(A)-1 :
            l.append(l[0])
            print 123
        else:
            for i in range(l[0]+1,len(A)):
                if A[i]!=target:
                    l.append(i-1)
                    return l
            l.append(len(A)-1)
        return l