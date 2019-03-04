<<<<<<< HEAD
=======

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

def numbercount(string):
    lsum=[]
    l=[]
    k=len((string))
    if k==1:
        l=[[1,string]]
        return "1"+string
    i=0
    while (i <=k - 1 ):
        if i  == k - 1:
            l.append([1,string[i]])
            break
        if string[i]==string[i+1]:
            if i+1==k-1:
                lsum.append(string[i])
                lsum.append(string[i+1])
                l.append([len(lsum),lsum[0]])
                lsum=[]
                break
            elif string[i+1]!=string[i+2]:
                lsum.append(string[i])
                lsum.append(string[i + 1])
                i=i+2
                l.append([len(lsum),lsum[0]])
                lsum=[]
            else:
                lsum.append(string[i])
                i=i+1
        else:
            l.append([1,string[i]])
            i=i+1
    str123=""
    for i in l:
        str123=str123+str(i[0])+str(i[1])
    return str123

print numbercount("1211")

def countandsay(n):
    if n==0:
        return "1"
    if n==1:
        return "11"
    for i in range(2,n+1):
        l=numbercount(countandsay(n-1))
    return l

for i in range(1,9):
    print countandsay(i)

l=[2,3,4,5,6]
print l.sort()

>>>>>>> b2c8fe39f4848214a06f6f2e3d530419fa354b16

l=[(10,10),(2,50),(3,100)]
k=[]
for i in range(len(l)):
    k.append(l[i][0])
k.sort()
m=[]
for  i in range(len(k)):
    for j in range(len(l)):
        if k[i]==l[j][0]:
            m.append((l[j]))

print m


