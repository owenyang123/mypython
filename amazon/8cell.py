
def cells(list1,n):
    l = []
    l.append(list1)
    for i in range(1,n+1):
        k=l[i-1]
        m=len(list1)*[0]
        print m
        for j in range(1,len(m)-1):
            if k[j-1]+k[j+1]==1:
                m[j]=1
        l.append(m)
    return l

print cells([1,1,1,0,1,1,1,1],1)
print cells([1,1,1,0,1,1,1,1],2)
print cells([1,1,1,0,1,1,1,1],3)