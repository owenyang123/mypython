
l=[(10,10),(2,50),(3,100)]
k=[]
for i in range(len(l)):
    k.append(l[i][0])
k.sort()
m=[]
for  i in range(len(k)):
    for j in range(len(l)):
        if k[i]==l[j][0]:
            m.append((l[j]))

print m


