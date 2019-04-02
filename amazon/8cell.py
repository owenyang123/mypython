
def cells(list1,n):
<<<<<<< HEAD
    l = []
    l.append(list1)
    for i in range(1,n+1):
        k=l[i-1]
        m=len(list1)*[0]
        print m
=======
    list2=[0]
    list2=list2+list1+[0]
    l = []
    l.append(list2)
    for i in range(1,n+1):
        k=l[i-1]
        m=len(list2)*[0]
>>>>>>> e8b38a412ecb2268da0e3ffdd8c3782ea992f962
        for j in range(1,len(m)-1):
            if k[j-1]+k[j+1]==1:
                m[j]=1
        l.append(m)
<<<<<<< HEAD
    return l

print cells([1,1,1,0,1,1,1,1],1)
print cells([1,1,1,0,1,1,1,1],2)
print cells([1,1,1,0,1,1,1,1],3)
=======
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
>>>>>>> e8b38a412ecb2268da0e3ffdd8c3782ea992f962
