def bwalloc(total,weight_list):
    weight_list.sort()
    lenth=len(weight_list)
    sumweight=sum(weight_list)
    leftbw=total%sumweight
    list1=[0]*lenth
    for i in range(lenth-1,-1,-1):
        list1[i]=(weight_list[i]*total)/sumweight
        list1[i]+=min(leftbw,weight_list[i])
        leftbw-=list1[i]
        if leftbw<=0:
            leftbw=0
    return list1

print bwalloc(923,[1,2,3,2,4,5,6])
