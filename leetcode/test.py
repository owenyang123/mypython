l=[1,2,3,4]
l.insert(2,4)
print l
class Queue:
    def __init__(self):
        self.items = []
        self.eyes="123"

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

def factors(n):
    k=0
    for  i in range(1,n+1):
        if i*i>=n:
            k=i
            break
        if n%i==0:
            yield i,n/i
    if k*k==n:
        yield k

for k in factors(100):
    print k,type(k)