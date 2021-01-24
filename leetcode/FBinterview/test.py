def generate_dict(filename):
    switch_data={}
    with open(filename, 'r') as file:
        for row in file.readlines():
            temp=[ i for i in row.replace("\n","").split(",") if i!=""]
            if temp and (temp[1].startswith("xe") or temp[1].startswith("ge")):
                if temp[0] not in switch_data:switch_data[temp[0]]={temp[1]:{"input":int(temp[2]),"output":int(temp[3])}}
                else:switch_data[temp[0]][temp[1]]={"input":int(temp[2]),"output":int(temp[3])}
    print switch_data
    return switch_data

def findhightalk(dict1):
    if not dict1:return []
    res=[]
    for i in dict1:
        temp = [i, 0]
        for j in dict1[i]:
            temp[1]+=dict1[i][j]["input"]+dict1[i][j]["output"]
        res.append(temp)
    return sorted(res,key=lambda x:x[1])

import itertools
l=[]
for i in range(8):
    for  k  in  itertools.combinations([1,2,3,4,5,6,2],2):
        l.append(list(k))
print l
print len(l)