def helper(num):
    k = 1
    n1 = 0
    while (num > k):
        k *= 7
        n1+=1
    n=0
    for i in range(6, 1, -1):
        temp = (k / 7) * i
        print temp,i
        if num > temp:
            n = i
            break
    return (n,n1-1)

print helper(100)