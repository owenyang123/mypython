import random

for i in range(1000):
    a=random.randint(100,999)
    b=random.randint(100,999)
    c=random.randint(100,999)
    d=random.randint(100,999)
    a,b=max(a,b),min(a,b)
    c, d = max(c, d), min(c, d)
    print str(a)+"+"+str(b)+"="+"           "+str(a) + "-" + str(b) + "="+"         "+str(c)+"+"+str(d)+"="+"           "+str(c) + "-" + str(d) + "="

print " "
print " "
