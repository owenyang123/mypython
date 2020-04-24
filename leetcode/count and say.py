class Solution:
    def countAndSay(self, n):
        if n==1:
            return "1"
        if n==2:
            return "11"
        for i in range(2,n+1):
            l=self.numbercount(self.countAndSay(i-1))
        return l
    def numbercount(self,string):
        lsum=[]
        l=[]
        k=len((string))
        if k==1:
            l=[[1,string]]
            return "1"+string
        i=0
        while (i <=k - 1 ):
            if i  == k - 1:
                l.append([1,string[i]])
                break
            if string[i]==string[i+1]:
                if i+1==k-1:
                    lsum.append(string[i])
                    lsum.append(string[i+1])
                    l.append([len(lsum),lsum[0]])
                    lsum=[]
                    break
                elif string[i+1]!=string[i+2]:
                    lsum.append(string[i])
                    lsum.append(string[i + 1])
                    i=i+2
                    l.append([len(lsum),lsum[0]])
                    lsum=[]
                else:
                    lsum.append(string[i])
                    i=i+1
            else:
                l.append([1,string[i]])
                i=i+1
        str123=""
        for i in l:
            str123=str123+str(i[0])+str(i[1])
        return str123
k=Solution()
print k.countAndSay(23)


