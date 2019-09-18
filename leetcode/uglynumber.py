class Solution:
    def nthUglyNumber(self, n):
        k=[1]
        x,y,z=0,0,0
        while (len(k)<n):
            temp=min(k[x]*2,k[y]*3,k[z]*5)
            k.append(temp)
            if k[x]*2==temp:
                x=x+1
            if k[y]*3==temp:
                y=y+1
            if k[z]*5==temp:
                z=z+1
        return k

k=Solution()
print k.nthUglyNumber(100)
