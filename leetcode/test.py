matrix=[[1,2,3,4],
        [6,7,8,9],
        [11,12,13,14],
        [16,17,18,19]]

def rotation(A):
    if A==[]:
        return None
    n=len(matrix)
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

print rotation([])
