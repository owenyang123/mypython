def swapnumber(num):
    if not num:return None
    str1=str(num)
    if len(str1)==1:
        return num
    list1=[x for x in str1]
    min1 = min(list1)
    if list1[0]==min1:
        return int(str(list1[0])+str(swapnumber(int("".join(list1[1:])))))
    for i in range(len(list1)-1,-1,-1):
        if list1[i]==min1:
            list1[0],list1[i]=list1[i],list1[0]
    return int("".join(list1))


print swapnumber(11111992)






class Solution1(object):
    def maximumSwap(self, num):
        str1=str(num)
        return int(self.helper(str1))
    def helper(self,str1):
        if len(str1)==1:
            return str1
        if str1[-1]==0:
            return self.helper(str[0:-1])+"0"
        list1=list(str1)
        maxstr=max(list1)
        if list1[0]==maxstr:
            return list1[0]+self.helper(str1[1:])
        for i in range(len(list1)-1,-1,-1):
            if list1[i]==maxstr:
                list1[0],list1[i]=list1[i],list1[0]
        return "".join(list1)

k=Solution1()
print k.maximumSwap(9973)


class Solution2():
    def swapnumber(self,num):
        if not num:return None
        str1=str(num)
        return int(self.helper(str1))
    def helper(self,str1):
        if len(str1)==1:return str1
        if str1[-1]=="0":return str1[0:-1]
        list1=[x for x in str1]
        minstr=min(list1)
        if list1[0]==minstr:
            return list1[0]+self.helper(str1[1:])
        for i in range(len(list1)-1,-1,-1):
            if list1[i]==minstr:
                list1[0],list1[i]=list1[i],list1[0]
        return "".join(list1)
k=Solution2()
print k.swapnumber(1199234)

<<<<<<< HEAD

print round((float(5)/3),2)

=======
print str.isalpha()
>>>>>>> c62e426afd51e1938a055f5d0c530bbb4980021c
