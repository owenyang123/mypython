from functools import reduce

def fn(x, y):
    return x * 10 + y

print reduce(fn, [1, 3, 5, 7, 9])

l=[1,2,3,4,5]
l.pop(1)
print l