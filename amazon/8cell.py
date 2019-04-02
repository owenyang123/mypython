
def cells(list1,n):
    list2=[0]
    list2=list2+list1+[0]
    l = []
    l.append(list2)
    for i in range(1,n+1):
        k=l[i-1]
        m=len(list2)*[0]
        for j in range(1,len(m)-1):
            if k[j-1]+k[j+1]==1:
                m[j]=1
        l.append(m)
    return l[-1][1:-1]


list1=[1,1,1,1,1,1,1,1]
t=0
l=list1=[1,1,1,1,1,1,1,1]
c=0
while (t==0):
    l=cells(l,1)
    if l==list1:
        t=1
        print c

    else:
        c=c+1
