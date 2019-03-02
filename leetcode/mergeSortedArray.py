class Solution:
    def mergeSortedArray(self, A, B):
        if len(B)==[]:
            return A
        if len(A)==[]:
            return B
        if len(A)>=len(B):
            a=A
            b=B
        else:
            a=B
            b=A
        i=0
        j=0
        c=[]
        while((i<=len(a)-1 or j<=len(b)-1)):
            if i==len(a):
                c.append(b[j])
                j=j+1
                print i, j, c
            elif j==len(b):
                c.append(a[i])
                i=i+1
                print i, j, c
            elif a[i]<=b[j] :
                c.append(a[i])
                i=i+1
                print i, j, c
            elif b[j]<a[i] :
                c.append(b[j])
                j=j+1
                print i, j, c
        return c

k=Solution()
print k.mergeSortedArray([1,3,5],[4])







