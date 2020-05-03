import random as ran
for i in ["a","b","c"]:
    globals()[i]=ran.randrange(100)
print a
print b
print c