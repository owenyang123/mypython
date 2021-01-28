class Solution:
    # @param A : integer
    # @return an integer
    def solve(self, A):
        if A==1 or A==2 :return 1
        if A==3:return 2
        temp1,temp2,temp3=3,2,1
        for i in range(4,A+1):
            temp1=temp2+temp3
            temp3=temp2
            temp2=temp1
            print temp1
        return temp1
k=Solution()
print k.solve(50)