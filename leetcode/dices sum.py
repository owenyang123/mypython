class Solution:
    def dicesSum(self, n):
        po=1.0
        for i in range(n):

            po=po*1.0/6.0
            po=(po*1.0)/6.0
        l=[1,2,3,4,5,6]
        l1={}
        l2=[0]*(n-1)
        self.dfs(l,l1,l2,n,n)
        result=[]
        for i in l1.keys():
            l1[i]=l1[i]*po
            result.append([i,l1[i]])
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
                if sum(l2+[i]) not in l1.keys():
                    l1[sum(l2+[i])]=1
                else:
                    l1[sum(l2+[i])]+=1
                l1.append(sum((l2+[i])))
            return l1
        else:
            for i in l :
                l2[n1-n]=i
                self.dfs(l,l1,l2,n-1,n1)



class Solution1:
    # @param {int} n an integer
    # @return {tuple[]} a list of tuple(sum, probability)
    def dicesSum1(self, n):
        # Write your code here
        def helper(n):
            if not n: return {}
            if n==1: return {i:1.0/6 for i in range(1,7)}
            result = {}
            rval = helper(n-1)
            for i in range(1,7):
                for key in rval:
                    s,p = (i+key),(1.0/6)*rval[key]
                    result[s] = result[s]+p if s in result else p
            return result
        mydict = helper(n)
        print mydict
        return [[key,mydict[key]] for key in mydict]
k=Solution1()
print k.dicesSum1(15)

k=Solution()
print k.dicesSum(7)

