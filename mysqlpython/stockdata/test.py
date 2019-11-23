with open("PFE.csv", 'r') as loglines:
    for line in loglines.readlines():
        k=line.replace("\n","").split(",")
        if k[2][0].isdigit():
            m=k[2]

for i in range(5,10):
    if i<=7:
        continue
    print i