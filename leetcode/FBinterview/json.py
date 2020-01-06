class Solution:
    # @param A : string
    # @return a list of strings
    def prettyJSON(self, A):
        if not A  or A[0]!="{":return ""
        l=[]
        temp=0
        for i in range(len(A)):
            if A[i]=="{":
                l.append(" "*temp+A[i])
                temp+=2
            elif A[i]=="[":
                l.append(" " * temp + A[i])
                temp+=2
            elif A[i]=="}":
                temp-=2
                l.append(" " * temp + A[i])
            elif A[i]=="]":
                temp-=2
                l.append(" " * temp + A[i])
            else:
                if A[i-1]=="{" or A[i-1]=="[" or A[i-1]==",":
                    l.append(" " * temp + A[i])
                else:
                    l[-1]=l[-1]+A[i]
        print l
        return "\n".join(l)


k=Solution()
strtest='{A:"B",C:{D:"E",F:{G:"H",I:"J"}}}'
print k.prettyJSON(strtest)
