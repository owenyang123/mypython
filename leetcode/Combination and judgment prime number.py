class Solution:
    """
    @param a: the n numbers
    @param k: the number of integers you can choose
    @return: how many ways that the sum of the k integers is a prime number
    """
    result=[]
    def getWays(self, a, k):
        self.sublist(a,k,[])
        count=0
        m=[]
        for i in self.result:
            sum=0
            for j in i:
                sum+=j
            if self.prime(sum) :
                m.append(sum)
        print self.result
        print m
        return len(m)
    def sublist(self,a,k,l):
        if k==0:
            l.sort()
            if l in self.result:
                return
            else:
                self.result.append(l)
                return
        for i in range(len(a)):
            if i==0:
                self.sublist(a[1:], k - 1,l+[a[i]])
            elif i==len(a)-1:
                self.sublist(a[0:-1], k - 1,l+[a[i]])
            else:
                self.sublist(a[0:i]+a[i+1:], k - 1, l+[a[i]])
    def prime(self,n):
        if n<2:
            return False
        if n==2:
            return True
        for i in range(2,n/2):
            if n%i==0:
                return False
        return True

k=Solution()
print k.getWays([3,9,23,12,34,65,32,19,81],4)