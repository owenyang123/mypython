def allpime(n):
    if n<=5 :return [i for i in [2,3,5] if i<=n]
    rootlist=[i for i in range(3,int(n**0.5+1)) if i%2==1]
    l=range(3,n+1)[0:-1:2]
    for i in range(len(l)):
        temp=[l[i]%j for j in rootlist if l[i]>j]
        if all(temp):continue
        l[i]=0
    return [2]+[i for i in l if i!=0]
print allpime(5)