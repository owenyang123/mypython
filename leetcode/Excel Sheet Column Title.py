class Solution:
    def convertToTitle(self, n):
        if n<=0 or n==None:
            return None
        l=[]
        if n<=26:
            return chr(n+64)
        while (n>=1):
           if n%26==0:
               r=26
               n=n-1
           else:
               r=n%26
           l.append(r)
           n=n/26
        str1=""
        for i in l[::-1]:
            str1=str1+chr(i+64)
        return str1