class Solution:

    def repeatedNumber(self, A):
        l1=list(A)
        l1.sort()
        l=[]
        for i in range(1,len(l1)+1):
            l.append(i)

        k=[]
        flag=1
        for i in range(len(l1)):
            if (l1[i]-l[i])==-1:
                k.append(l1[i])
                k.append(l[i])
                flag=0
            elif (l1[i]-l[i])==1:
                k.append(l[i])
        if flag==1:
            return [k[-1]+1,k[0]]
        else:
            return [k[0],k[-1]]

test1=(3,1,2,5,3)
k=Solution()
print k.repeatedNumber(test1)