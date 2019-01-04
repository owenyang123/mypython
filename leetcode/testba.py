def sumlist(l,n):
    sum=0
    for i in range(n+1):
        sum=sum+int(l[i])
    return sum
list1=[0,0,0,1,1,1]
n=16+1
for i in range(6,n):
    x=sumlist(list1,i-3)+1
    list1.append(x)
print list1[n-1]