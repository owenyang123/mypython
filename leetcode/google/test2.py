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

def numberstps(x,y):
    print x,y
    if x==0 and y==0:return 0
    if x==1 and y==0:return 1
    if x>0 and y<0 and x+y==1:
        l = [1] + [i * 8 for i in range(1, x)]
        return sum(l)
    if abs(x)==abs(y) and x>0:
        if y<0:return numberstps(x+1,y)-1
        return numberstps(y,1-y)+y-1+y
    if abs(x)==abs(y) and x<0:
        if y>0:return numberstps(-x,-y+1)+3*abs(x)+abs(-y+1)
        return numberstps(-y+1,y)-2*abs(x)-1
    if abs(x)==max(abs(x),abs(y)):
        if x>0:
            if y>=0:return numberstps(x,x)-abs(x)+y
            return numberstps(x,-x+1)+abs(-x+1-y)
        if x<0:
            if y>=0:return numberstps(x,-x)+abx(-x-y)
            return numberstps(x,x)-abs(x-y)
    if abs(y) == max(abs(x), abs(y)):
        if y>0:
            if x>=0:return numberstps(y,y)+abs(y)-abs(x)
            return numberstps(y,-y)-abs(y)+abs(x)
        if y<0:
            if x>0:return numberstps(-y,y)-abs(y)+abs(x)
            return numberstps(y,y)+abs(y)-abs(x)

print numberstps(100000,100000)