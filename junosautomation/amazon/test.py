'''
l=[0, 1, 7, 2, 0, 0, 0, 0, 0, 0]
def allin1(l):
    if sum(l)!=len(l):return False
    if l==[0,2] or l==[2,0]:return 1
    if len([1 for i in l if i==1])==len(l):return 0
    else:
        temp=[True if sum(l[0:i+1])==len(l[0:i+1]) else False for i in range(len(l))]
        if temp.count(True)>=2:
            for i in range(len(temp)):
                if temp[i]:return allin1(l[0:i+1])+allin1(l[i+1:])
        else:
            #if l[0]==1:return allin1(l[1:])
            if l[0]==0:
                for i in range(len(l)):
                    if l[i]>1:
                        l[i]-=1
                        return i+allin1(l[1:])
            return l[0]-1+allin1([l[1]+l[0]-1]+l[2:])
def set_plate(plates):
    res, s = [], 0
    for i, p in enumerate(plates):
        s += p
        res.append(i + 1 - s)
    return sum(abs(r) for r in res)
print set_plate(l)
print allin1(l)
'''
def numberstps(x,y):
    print (x,y)
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
            if y>=0:return numberstps(x,-x)+abs(-x-y)
            return numberstps(x,x)-abs(x-y)
    if abs(y) == max(abs(x), abs(y)):
        if y>0:
            if x>=0:return numberstps(y,y)+abs(y)-abs(x)
            return numberstps(y,-y)-abs(y)+abs(x)
        if y<0:
            if x>0:return numberstps(-y,y)-abs(y)+abs(x)
            return numberstps(y,y)+abs(y)-abs(x)

print numberstps(999,999)













