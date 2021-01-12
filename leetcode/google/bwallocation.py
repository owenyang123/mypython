def bwalloc(total,weight_list):
    lenth=len(weight_list)
    weight_list.sort(reverse=True)
    sumweight=sum(weight_list)
    leftbw=total%sumweight
    list1=[0]*lenth
    for i in range(lenth):
        list1[i]=weight_list[i]*(total/sumweight)
        list1[i]+=min(leftbw,weight_list[i])
        leftbw-=min(leftbw,weight_list[i])
    return list1,sum(list1)



print bwalloc(927,[2,2,2,1,3,3,3,4,8])

