l= [[1] * 8 for i in range(8)]
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
    while(r2<len1-1 and c2<len1-1):
        r2=r2+1
        c2=c2+1
        A[r2][c2] = 0
    while(r3<len1-1 and c3>=1):
        c3=c3-1
        r3=r3+1
        A[r3][c3] = 0
    while(r4>=1 and c4<len1-1):
        r4=r4-1
        c4=c4+1
        A[r4][c4] = 0
    A[r][c] = 1
    return A

count1=0


def dp(A,r,k):
    for i in range(len1):
        if A[r][i]==1:
            set1(A, r, i)
            B=A
            if r==6 and (1 in A[r+1]):
                r=0
                k=k+1
                A = [[1] * 8 for j in range(8)]
                print r, i
                return
            elif r==6:
                r=0
                A=[[1] * 8 for j in range(8)]
                print r, i
                return
            elif A[r]==[0,0,0,0,0,0,0,0] or A[r+1]==[0,0,0,0,0,0,0,0]:
                dp(B,r,i+1)
            else:
                r=r+1
                dp(A,r,k)
        else:
            pass
print dp(l,0,0)

