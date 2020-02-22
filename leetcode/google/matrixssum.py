def matrixsum(mat,b):
    row=len(mat)
    col=len(mat[0])
    if b[0]>row-1 or b[1]>col-1:
        return -1
    sum=0
    for i in range(b[1]+1):
        sum+=mat[0][i]+mat[b[0]][i]
    for i in range(1,b[0]):
        sum+=mat[i][0]+mat[i][b[1]]
    return sum

def matrixsum1(mat,b):
    row=len(mat)
    col=len(mat[0])
    if b[0]>row-1 or b[1]>col-1:
        return -1
    sum=0
    for i in range(0,b[0]+1):
        for j in range(0,b[1]+1):
            if (0<i<b[0]) and (0<j<b[1]):
                continue
            sum+=m[i][j]
    return sum



m=[[1, 4, 6, 4, 1],
 [1, 4, 6, 4, 1],
 [1, 4, 6, 4, 1],
 [1, 4, 6, 4, 1],
 [1, 4, 6, 4, 1]]
print matrixsum1(m,[4,4])