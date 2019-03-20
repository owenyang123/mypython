l= [[1] * 4 for i in range(4)]
len1=len(l)


def set1(A,r,c):
    K=A
    len1= len(A)
    for i in range(len(A)):
        A[r][i]=0
        A[i][c]=0
    r1=r
    c1=c
    r2=r
    c2=c
    r3=r
    c3=c
    r4=r
    c4=c
    while(r1>=1 and c1>=1):
        r1=r1-1
        c1=c1-1
        A[r1][c1] = 0
    while(r2<len1 and c2<len1):
        A[r2][c2] = 0
        r2=r2+1
        c2=c2+1
    while(r3<len1 and c3>=1):
        c3=c3-1
        r3=r3+1
        A[r3][c3] = 0
    while(r4>=1 and c4<len1):
        r4=r4-1
        c4=c4+1
        A[r4][c4] = 0
    A[r][c] = 1
    return A

count1=0
B=l

def dp(A,r,k):
    for i in range(len1):
            set1(A, r, i)
            if r==2 and (1 in A[r+1]):
                r=0
                k=k+1
                print "x", A,r,k,i
                A = [[1] * 4 for j in range(4)]
            elif r==2:
                r=0
                print "y",A,r,i
                A=[[1] * 4 for j in range(4)]

            else:
                r=r+1
                print "z",A,r,i
                dp(A,r,k)
print dp(l,0,0)

