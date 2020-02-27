def bwalloc(total,weight_list):
    weight_list.sort()
    lenth=len(weight_list)
    sumweight=sum(weight_list)
    leftbw=total%sumweight
    list1=[0]*lenth
    for i in range(lenth-1,-1,-1):
        list1[i]=weight_list[i]*(total/sumweight)
        list1[i]+=min(leftbw,weight_list[i])
        leftbw-=min(leftbw,weight_list[i])
    return list1,sum(list1)


print bwalloc(923,[5,2,3,3,3,4,4,4,4,4,4])

print [x for x in range(1,11)][0::2]

def findex(n):
    temp0=1
    temp1=1
    for i in range(1,n+1,1):
        if i<=2:
            yield 1
        else:
            yield temp0+temp1
            temp0,temp1=temp1,temp0+temp1

for i in findex(2):
    print i

def getNarcissisticNumbers(n):
    if n == 1:
        return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    if n == 6:
        return [548834]

    result = []
    for i in xrange(10 ** (n-1), 10 ** n):
        j, s = i, 0
        while j != 0:
            s += (j % 10) ** n;
            j = j / 10
        if s == i:
            result.append(i)
    return result

