def power123(a,b):
    if a==1:
        return 1
    if b==0:
        return 1
    if b==1:
        return a
    if b<0:
        return 1.0000/float(power123(a,-b))
    if b%2==0:
        return power123(a,b/2)*power123(a,b/2)
    else:
        return power123(a, b / 2) * power123(a, b / 2)*a

print power123(3,-15)


print "1213132".join("asde")


for i in range(5):
    if i==3:
        continue
    print i
