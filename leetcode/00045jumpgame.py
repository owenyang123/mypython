import numpy as np
import random
#dfs to list all path from s to d#
testcase=[3]

for i in range(15):
    testcase.append(random.randrange(1, 6))
print testcase
def dfs_paths(graph,root,target,path=None):
    if path is None:
        path=[root]
    if root==target:
        yield path
    for vertex in [x for x in graph[root] if x not in path]:
        for each_path in dfs_paths(graph,vertex,target,path+[vertex]):
            yield each_path
def neighborlist(n):
    l=[]
    for x in range(len(n)):
        if x==(len(n)-1):
            l.append([x,-1])
        elif n[x]==0:
            l.append([x, -1])
        else:
            for i in range(1,(n[x]+1)):
                if (x+i)>(len(n)-1):
                    l.append([x, -1])
                else:
                    l.append([x,x+i])
    return l
def graphmade(list,n):
    graph={}
    for i in range(len(n)):
        l=[]
        l1=[]
        for x in list:
            if x[1]==-1:
                pass
            if x[0]==i:
                l.append(x[1])
        for x in l:
            if x!=-1:
                l1.append(x)
        graph.update({i:l1})
    return graph
nlist=neighborlist(testcase)
nlistgraph=graphmade(nlist,testcase)
y= list(dfs_paths(nlistgraph,0,(len(testcase)-1)))
pathhop=[]
index=0
for i in np.array(y):
    pathhop.append(len(i))
print min(pathhop)
for i in np.array(y):
    if len(i)==min(pathhop):
        print i
    else:
        pass
#done#