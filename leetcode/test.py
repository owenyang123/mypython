def myfact(n):
    if n < 2:
        return 1
    else:
        return n * myfact(n-1)
def getrank(m):
    if len(m)==1:
        return 1
    if len(m)==2:
        if m[0]<m[1]:
            return 1
        return 2
    sum=0
    for i in range(len(m)):
        num=0
        if i==len(m)-2:
            if m[i]>m[-1]:
                sum=sum+2
            else:
                sum=sum+1
            break
        else:
            for j in range(i+1,len(m)):
                if m[j]<m[i]:
                    num=num+1
            sum=sum+num*myfact(len(m)-i-1)
    return sum
m=[8,9,7,4,5,1]
print getrank(m)





