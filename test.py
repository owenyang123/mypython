l= [[0] * 8 for i in range(8)]

def set1(A,r,c):
    K=A
    len1= len(A)
    for i in range(len(A)):
        A[r][i]=1
        A[i][c]=1
    r1=r
    c1=c
    r2=r
    c2=c
    while(r2<len1 and c2<len1):
        A[r2][c2] = 1
        r2=r2+1
        c2=c2+1
    while(r1>=1 and c1>=1):
        r1=r1-1
        c1=c1-1
        A[r1][c1] = 1
    c = c + 1
    if c<len1:
        for i in range(len1):
            if A[i][c]==0:
                set1(A,i,c)
                for j in range(len1):
                    if A[j][len1-1]==0:
                        print A
            else:
                A=K
                pass
def dpqueue(A):
    K=A
    len1, len2 = len(A), len(A[0])
    for i in range(len1):
        A=K
        set1(A,i,0)


print dpqueue(l)
