class SR_input():
    def findpath(self,topology,start,end):
        if not topology:return []
        if start==end:return [[end]]
        self.path=[]
        self.dfsroute(topology,end,[start])
        return self.path
    def dfsroute(self,topology,end,temppath):
        if end==temppath[-1]:
            self.path.append(temppath)
            return
        for i in topology[temppath[-1]]:
            if i in set(temppath):continue
            self.dfsroute(topology, end, temppath+[i])

test=SR_input()
topology={1:[2,3,4],2:[1,3,5],3:[1,2,4,5],4:[1,3,5],5:[2,3,4,6],6:[5]}

print sorted(test.findpath(topology,1,6),key=lambda x:len(x))
