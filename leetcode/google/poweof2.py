class Solution:
    # @param A : string
    # @return an integer
    def power(self, A):
        if int(A)==2:
            return 1
        if int(A)%2!=0:
            return 0
        return self.power(str(int(A)/2))

class Solution1:
    # @param A : string
    # @return an integer
    def power(self, A):
        if int(A)<=1:
            return 0
        if int(A)==2 :
            return 1
        k=int(A)
        if k&(k-1)==0:
            return 1
        return 0

k=Solution()
print k.power("1024")
print "1"+"\n"
print 2