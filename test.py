def log(func):
    def wrapper(*args, **kw):
        print('11111call %s():' % func.__name__)
        return func(*args, **kw)
    return wrapper
@log
def now():
    print('2015-3-25')

def validy(x,y,l):
    if (x-1,y-1) in l and (x-1,y+1) in l and (x+1,y) in l :return (0,x,y)
    if (x-1,y-1) in l and (x+1,y-1) in l and (x,y+1) in l :return (1,x,y)
    if (x-1,y+1) in l and (x+1,y+1) in l and (x,y-1) in l :return (2,x,y)
    if (x +1, y -1) in l and (x + 1, y + 1) in l and (x-1 , y) in l: return (3,x,y)
    return -1

def main(list1):
    grid=list1[0]
    step=[((i-1)//grid,(i-1)%grid) for i in list1[1:]]
    p1,p2,set1,set2=step[0::2],step[1::2],set(),set()
    count1,count2,f1,f2=0,0,False,False
    temp1,temp2=(),()
    for i in p1:
        set1.add(i)
        count1+=1
        for j in set1:
            if validy(j[0],j[1],set1)==-1:continue
            temp1=validy(j[0],j[1],set1)
            f1=True
            break
        if f1:break
    for i in p2:
        set2.add(i)
        count2+=1
        for j in set2:
            if validy(j[0],j[1],set2)==-1:continue
            temp2=validy(j[0],j[1],set2)
            f2=True
            break
        if f2:break
    if not f1 and not f2:return 0
    if not f2:res=temp1
    if not f1:res=temp2
    if f1 and f2 and count1<=count2:res=temp1
    elif f1 and f2:res=temp2
    if res[0]==0:return grid*res[1]+res[2]+grid*(res[1]-1)+res[2]-1+grid*(res[1]-1)+res[2]+1+grid*(res[1]+1)+res[2]+4
    if res[0] == 1: return grid * res[1] + res[2] + grid * (res[1] - 1) + res[2] - 1 + grid * (res[1] +1) + res[
        2] - 1 + grid * (res[1] ) + res[2]+1 + 4
    if res[0] == 2: return grid * res[1] + res[2] + grid * (res[1] - 1) + res[2] + 1 + grid * (res[1] +1) + res[
        2] + 1 + grid * (res[1] ) + res[2]-1 + 4
    if res[0] == 3: return grid * res[1] + res[2] + grid * (res[1] +1) + res[2] - 1 + grid * (res[1] +1) + res[
        2] + 1 + grid * (res[1] - 1) + res[2] + 4


def rmothers(str1):
    temp=[i for i in str1 if i.isalnum()]
    return "".join(temp)

def sorting(str1):
    print(str1)
    if not str1:return 0
    if str1==sorted(str1):return 0
    stack=[ord(i) for i in sorted(str1)][0]
    temp=list(str1)
    if ord(str1[0])==stack:return sorting(str1[1:])
    p=0
    for i in range(len(str1)):
        if ord(str1[i])==stack:
            p=i
            break
    temp[0],temp[p]= temp[p],temp[0]
    return 1+sorting("".join(temp[1:]))

print(sorting(rmothers("10 Java Programs")))