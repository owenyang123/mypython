
def generate_dict(filename):
    switch_data={}
    with open(filename, 'r') as file:
        for row in file.readlines():
            temp=[ i for i in row.replace("\n","").split(",") if i!=""]
            if temp and temp[2].isdigit():
                if temp[0] in switch_data:switch_data[temp[0]].append([temp[1],int(temp[2]),int(temp[3])])
                else:switch_data[temp[0]]=[[temp[1],int(temp[2]),int(temp[3])]]
    return switch_data
def findhightalk(dict1):
    if not dict1:return []
    res=[]
    for i in dict1:
        temp = [i, 0]
        for j in zip(*dict1[i])[1:]:
            temp[1] += sum(j)
        res.append(temp)
    return sorted(res,key=lambda x:x[1])[-1]
print findhightalk(generate_dict('switch.csv'))