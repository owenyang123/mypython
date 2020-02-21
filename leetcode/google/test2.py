def swapnumber(num):
    if not num:return None
    str1=str(num)
    if len(str1)==1:
        return num
    list1=[x for x in str1]
    if list1[0]==min(list1):
        return int(str(list1[0])+str(swapnumber(int("".join(list1[1:])))))
    min1=min(list1)
    for i in range(len(list1)-1,-1,-1):
        if list1[i]==min1:
            list1[0],list1[i]=list1[i],list1[0]
    return int("".join(list1))

print swapnumber(1992)

