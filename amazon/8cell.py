l = []
def cells(list1,n):
    if n==0:
        l.append(list1)
        return l[-1]
    else:
        k=[]
        m=[]
        for i in range(1,len(cells(list1,n-1))-1):
            if cells(list1,n-1)[i-1]+cells(list1,n-1)[i+1]==1:
                k.append(i)
        for i in range(len(cells(list1,n-1))):
            if i in k:
                m.append(1)
            else:
                m.append(0)
        l.pop(0)
        l.append(m)
        return l[-1]


list1=[0, 0, 0, 1, 1, 0, 1, 0]
print  cells(list1,1)
print  cells(list1,2)
print  cells(list1,3)
