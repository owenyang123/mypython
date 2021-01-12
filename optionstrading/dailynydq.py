import seaborn as sns
import basictools as bt
import stockplay as sp
import csv
sns.set(style="whitegrid")
capset=set()
with open('gt10blist') as f:
    for i in f.readlines():
        if "-" not in i and "." not in i:
            capset.add(i.replace("\n",""))
l=sp.caifuziyou(list(capset))
filename_tod="ND"+bt.get_data(0)+".csv"
filename_yes="ND"+bt.get_data(1)+".csv"
set_tod=set([])
set_yes=set([])
with open(filename_tod, 'w') as fd:
    for t in l:
        if t[-1] != 0 :
            set_tod.add(t[0])
            writer = csv.writer(fd)
            writer.writerow(t)
with open(filename_yes) as fd:
    for i in fd.readlines():
        if len(i) > 10:
            set_yes.add(i.replace("\n", "").split(",")[0])
temp1=[]
for i in l:
    if i[0] not in set_yes and i[0] in set_tod:
        temp1.append([i[0],i[1],i[2]])
temp1.sort(key=lambda x:x[-1],reverse=True)
for i in temp1:
    print(i)
