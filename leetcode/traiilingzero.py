class Solution:
    def trailingZeros(self, n):
        number5=0
        while(n!=0):
            n=n/5
            number5=number5+n
        return number5

test1=Solution()
print test1.trailingZeros(35)
