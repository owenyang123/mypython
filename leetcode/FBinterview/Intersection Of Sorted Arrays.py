class Solution:
    # @param A : tuple of integers
    # @param B : tuple of integers
    # @return a list of integers
    def intersect(self, A, B):
        if B==[] and A==[]:
            return []
        elif B==[] and A:
            return []
        elif A==[] and B:
            return []
        if len(A)>=len(B):
            l1=A
            l2=B
        else:
            l1=B
            l2=A
        l=[]
        i1,j1=0,len(l1)-1
        i2,j2=0,len(l2)-1
        while (i2-1<j2 and i1-1<j1):
            if l2[i2]==l1[i1]:
                l.append(l2[i2])
                i1+=1
                i2+=1
            elif l2[j2]==l1[j1]:
                l.append(l2[j2])
                j1-=1
                j2-=1
            else:
                i1+=1
                j1-=1
            print l
        l.sort()
        return l

k=Solution()
A=[1]
B=[1]
print k.intersect(A,B)