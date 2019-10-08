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


print ".".join("asde")


for i in range(5):
    if i==3:
        continue
    print i
l1=[1,2,3,4,5,6,7,8,9,0]

print l1[1:9:2]

