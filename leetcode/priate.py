def coin(n,m):
    if m<n:
        return 0
    elif m==n:
        return 1
    elif n==1:
        return 1
    elif n==2:
        return m/2
    else:
        sum=0
        for i in range(1,n+1):
            sum+=coin(i,m-n)
        return sum

print coin(3,10)