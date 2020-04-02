l=[]
with open("cfm", 'r') as loglines:
    for line in loglines.readlines():
        l.append(line)

x=[i for i in range(len(l)) if "0x10: 89 02" in l[i]]
set1=set()
for i in x :
    temp=l[i-1].replace(" ","")[-33:-21].replace("\n","")
    if temp not in set1:set1.add(temp)
print set1