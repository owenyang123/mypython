teststr="11223344"
def bfslist(ipstr,n):
    if ipstr=="" or  n>len(ipstr):
        return None
    list1=[]
    list2=[]
    for i in range(3):
        if i<len(ipstr[n:]) and ipstr[n]!="0" and int(ipstr[n:n+i+1])<256:
            list1.append(ipstr[0:n]+"."+ipstr[n:n+i+1])
            list2.append(ipstr[n+i+1:])
    return list1,list2

l1=bfslist(teststr,1)
l2=bfslist(teststr,2)
l3=bfslist(teststr,3)

for i in range(len(l1[1])):
    ll1=bfslist(l1[1][i],1)
    ll2= bfslist(l1[1][i], 2)
    ll3= bfslist(l1[1][i], 3)
    for j in ll1[1]:
        print l1[0][i]+"."+j
    for j in ll2[1]:
        print ll2[0][i]+"."+j
    for j in ll3[1]:
        print ll3[0][i]+"."+j




