def power123(a,b):
    if a==0:
        return 0
    if a==1 :
        return 1
    if b==0 :
        return 1
    if b<0 :
        return 1/power123(a,-b)
    if b%2==0:
        return power123(a,b/2)*power123(a,b/2)
    else:
        return power123(a,b/2)*power123(a,b/2)*a


print power123(2,10)
