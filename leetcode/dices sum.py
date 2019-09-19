class Solution:
    def dicesSum(self, n):
        po=1.0
        for i in range(n):
            po=(po*1.0)/6.0
        l=[1,2,3,4,5,6]
        l1=[]
        l2=[0]*(n-1)
        self.dfs(l,l1,l2,n,n)
        dict1={}
        for i in l1:
            if i not in dict1.keys():
                dict1[i]=po
            else:
                dict1[i]+=po
        result=[]
        for i in dict1.keys():
            result.append([i,dict1[i]])
        return result
    def dfs(self,l,l1,l2,n,n1):
        if n==1:
            for i in l:
                l1.append(sum((l2+[i])))
            return l1
        else:
            for i in l :
                l2[n1-n]=i
                self.dfs(l,l1,l2,n-1,n1)


k=Solution()
print k.dicesSum(7)