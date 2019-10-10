def getfactor(n):
    l=[]
    if n==0 or not n:
        return []
    l.append(1)
    if n%2==0:
        l.append(2)
    for  i in range(3,n/2+1):
        if n%i==0:
            l.append (i)
    l.append(n)
    return l
def minfactors(list1):
    if not list1:
        return ""
    list1.sort()
    l2=getfactor(list1[0])
    for i in list1[1:]:
        for j in range(len(l2)):
            if i%l2[j] !=0:
                return l2[j-1]
    return l2[-1]

print minfactors([15,27,81,99,101])