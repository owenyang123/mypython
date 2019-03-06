<<<<<<< HEAD
matrix=[[1,2,3,4],
        [6,7,8,9],
        [11,12,13,14],
        [16,17,18,19]]

def rotation(A):
    if A==[]:
        return None
    n=len(matrix)
=======
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
>>>>>>> 0598fa66911ea576147b7c0fce7e63145db73963
    l=[]
    for x in range(n):
        l.append([0])
    for x in l:
        for i in range(n-1):
            x.append(0)
    for x in range(n):
        for y in range(n):
            l[x][y]=A[n-y-1][x]
    return l

<<<<<<< HEAD
print rotation([])
=======
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


>>>>>>> 0598fa66911ea576147b7c0fce7e63145db73963
