class Solution:
    def plusOne(self, A):
        if A==[0]:
            return [1]
        if A[0]==0 and len(A)>=2:
            return self.plusOne(A[1:])
        if A[-1]<=8:
            A[-1]+=1
            return A
        else:
            for i in range(len(A)):
                if A[len(A)-1-i]==9:
                    A[len(A)-1-i]=0
                    if len(A)-1-i==0:
                        return [1]+A
                else:
                    A[len(A)-1-i]+=1
                    return A
k=Solution()
print k.plusOne([0,0,9,9,9,9,2])