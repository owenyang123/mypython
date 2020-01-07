<<<<<<< HEAD
l=[1,2,3,4,5]
print l[:]
=======
from functools import reduce

def fn(x, y):
    return x * 10 + y

print reduce(fn, [1, 3, 5, 7, 9])

l=[1,2,3,4,5]
l.pop(1)
print l
>>>>>>> 8b80006fc7e54337c4a80386ba17de20f1664c2b
