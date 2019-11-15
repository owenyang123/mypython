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
            if A[0]==9 and len(set(A))==1:
                return [1]+[0]*len(A)
            for i in range(len(A)):
                if A[len(A)-1-i]==9:
                    A[len(A)-1-i]=0
                else:
                    A[len(A)-1-i]+=1
                    return A
k=Solution()
print k.plusOne([9,9,9,9,6])

def plusOne1(list1):
    if list1[0]=="0" and len(list1)>=2:
        return plusOne1(list1[1:])
    tem_str="".join(list1)
    tem_int=int(tem_str)+1
    tem_str=str(tem_int)
    return list(tem_str)
print plusOne1(["0","9","9","9","9"])