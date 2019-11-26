with open("PFE.csv", 'r') as loglines:
    for line in loglines.readlines():
        k=line.replace("\n","").split(",")
        if k[2][0].isdigit():
            m=k[2]

def printn(n):
    for i in range(1,n+1):
        yield i

k=printn(10)
print type(k)
for i in  k:
    print i