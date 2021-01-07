def fb123(list1):
    dict1={}
    for i in list1:
        temp="".join(sorted(i))
        if temp in dict1:dict1[temp].append(i)
        else:dict1[temp]=[i]
    return [ list(set(dict1[i])) for i in dict1]

list1=["star","rats","car","arts","arc","stars"]
print fb123(list1)


class Solution:
    def Closest(self, num, target):
        if not num:return []
        self.l=[]
        self.dfs(num,[])
        print len(self.l)
        res1=[[abs(sum(i)-target),i] for i in self.l]
        res1.sort(key=lambda x:x[0])
        res=[i  for i in res1 if i[0]==res1[0][0]]
        res.sort(key=lambda x:len(x[1]))
        return res[0][1]
    def dfs(self,num,temp):
        if len(num)==1:
            self.l.append(temp+num)
            return
        for i in range(len(num)):
            self.l.append(temp+[num[i]])
            self.dfs(num[i+1:],temp+[num[i]])





