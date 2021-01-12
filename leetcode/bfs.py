dict1={1:[2,3,4],2:[3,4],3:[5],4:[5],5:[]}
def dfstm(dict1,start,end):
    if start not in dict1 or end not in dict1:return []
    pathlist=[]
    q=[[start,[]]]
    while (q):
        print q
        node,path=q.pop(0)
        if node==end:
            pathlist.append(path+[node])
            continue
        for x in dict1[node]:
            q.append([x,path+[node]])
    return pathlist
x=dfstm(dict1,1,5)
print [2,3,4]>5
