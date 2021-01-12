switch_data={}
with open('switch.csv', 'r') as file:
    for row in file.readlines():
        temp=row.replace("\n","").split(",")
        if temp[2].isdigit():
            if temp[0] in switch_data:
                switch_data[temp[0]].append([temp[1],int(temp[2]),int(temp[3])])
            else:switch_data[temp[0]]=[[temp[1],int(temp[2]),int(temp[3])]]
def findhightalk(dict1):
    if not dict1:return []
    res=[]
    for i in dict1:
        temp = [i, 0]
        for j in zip(*switch_data[i])[1:]:
            temp[1] += sum(j)
        res.append(temp)
    return sorted(res,key=lambda x:x[1])[-1]
print findhightalk(switch_data)
