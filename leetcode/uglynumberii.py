class Solution(object):
    def nthUglyNumber(self, n):
        list1 = [1]
        p2,p3,p5=0,0,0
        for i in range(1,n):
            temp=min(list1[p2]*2,list1[p3]*3,list1[p5]*5)
            if temp==list1[p2]*2:p2+=1
            if temp == list1[p3] * 3: p3 += 1
            if temp == list1[p5] * 5: p5 += 1
            list1.append(temp)
        print list1
        return list1[-1]






k=Solution()

print k.nthUglyNumber(10)