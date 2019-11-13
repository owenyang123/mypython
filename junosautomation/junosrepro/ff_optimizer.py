#!/usr/bin/python
import sys,os,re,getopt,time,pprint,operator

f = open(sys.argv[1],"r")
f_list = []
filename= "optimized_" + sys.argv[1]
fd = open(filename,"a")

for line in f:
    f_list.append(line.rstrip('\r\n'))

regex = re.compile(r"term\s+(\S+)")
l = list(set([m[0] for l in f_list for m in [regex.findall(l)] if m]))

filter_dict = {}

for x in l:
    term_list = []
    for line in f_list:
        if x in line:
            term_list.append(line)
    
    tuple = ""
    count = 0
    search1 = ["source-prefix-list","source-address"]
    if any(s in l for l in term_list for s in search1):
        tuple +="sa"
        count += 1
    search2 = ["destination-prefix-list","destination-address"]
    if any(s in l for l in term_list for s in search2):
        tuple +="da"
        count += 1
    search3 = ["protocol"]
    if any(s in l for l in term_list for s in search3):
        tuple +="pr"
        count += 1
    search4 = ["source-port"]
    if any(s in l for l in term_list for s in search4):
        tuple +="sp"
        count += 1
    search5 = ["destination-port"]
    if any(s in l for l in term_list for s in search5):
        tuple +="dp"
        count += 1
    if (not tuple):
        count = 6
    filter_dict.update({x:[str(count)+tuple,term_list]})


#pprint.pprint(filter_dict) # enable for debug

sorted = sorted(filter_dict.items(), key=operator.itemgetter(1))
#pprint.pprint(sorted) #enable for debug
for item in sorted:
    for line in item[1][1]:
        print(line)
    fd.write("\n".join(item[1][1]))
    fd.write("\n")

fd.close()
f.close()

