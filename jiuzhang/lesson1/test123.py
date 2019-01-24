def towerOfHanoi(self, n):
    l = []
    l1 = []
    l2 = []
    k = []
    m = []
    if n == 1:
        l.append("from A to C")
        return l
    for i in range(2, n + 1):
        l1 = towerOfHanoi(self, i - 1)
        l2 = towerOfHanoi(self, i - 1)
        k = switch(l1, "B", "C")
        k.append("from A to C")
        m = switch(l2, "A", "B")
        k = k + m
        if i == n:
            return k


def switch(l, a, b):
    l1 = []
    l1 = l
    for i in range(len(l1)):
        l1[i] = l1[i].replace(a, "Z")
        l1[i] = l1[i].replace(b, a)
        l1[i] = l1[i].replace("Z", b)
    return l1

steps=towerOfHanoi("self",11)
print steps