import csv
l=[]
with open('ymh.csv') as fd:
    for i in fd.readlines():
        l.append(i.replace("\n","").split(","))
l.sort(key=lambda x:x[-3])
print l