class Solution:
    def reverseWords(self, s):
        if s=="" or s==" " or not s:
            return ""
        l1=s.split(" ")
        print l1
        len1=len(l1)
        result =""
        for i in xrange(len1-1,-1,-1):
            if l1[i]=="":
                pass
            elif i!=0:
                result=result+str(l1[i])+" "
            else:
                result = result + str(l1[i])
        return result


x="This won iz correkt. It has, No Mistakes et Oll. But there are two BIG mistakes in this sentence. and here is one      more."
k=Solution()
print k.reverseWords(x)



print str(bin(100))[2:]