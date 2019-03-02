import math
class Solution:
    def aplusb(self, a, b):
        while(b!=0):
            carry=a & b
            a=a^b
            b=carry<<1
        return a

k=Solution()
print k.aplusb(5,6)
print math.log(100,10)

