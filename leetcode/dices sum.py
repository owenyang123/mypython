class Solution:
    def dicesSum(self, n):
        po=1
        for i in range(n):
            po=po*0.17
        l=[1,2,3,4,5,6]
        l1=[]
        l2=[0]*(n-1)
        self.dfs(l,l1,l2,n,n)
        dict1={}
        for i in l1:
            if sum(i) not in dict1.keys():
                dict1[sum(i)]=po
            else:
                dict1[sum(i)]+=po
        result=[]
        for i in dict1.keys():
            result.append([i,round(dict1[i],2)])
        return result
    def dfs(self,l,l1,l2,n,n1):
        if n==1:
            for i in l:
                l1.append((l2+[i]))
            return l1
        else:
            for i in l :
                l2[n1-n]=i
                self.dfs(l,l1,l2,n-1,n1)


k=Solution()
print k.dicesSum(4)