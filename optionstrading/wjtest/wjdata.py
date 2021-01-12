dictapr,dictmay,dictjun,setall={},{},{},set()
'''
Build dict and set 
'''
with open('apr.csv', 'r') as file:
    for row in file.readlines():
        if row and row[0].isalpha():
            temp=row.replace("\n","").replace("\r","").split(',')
            dictapr[temp[0]]=float(temp[1])
            setall.add(temp[0])

with open('may.csv', 'r') as file:
    for row in file.readlines():
        if row and row[0].isalpha():
            temp=row.replace("\n","").replace("\r","").split(',')
            dictmay[temp[0]]=float(temp[1])
            setall.add(temp[0])

with open('jun.csv', 'r') as file:
    for row in file.readlines():
        if row and row[0].isalpha():
            temp=row.replace("\n","").replace("\r","").split(',')
            dictjun[temp[0]]=float(temp[1])
            setall.add(temp[0])

'''
if key not exist ,set it to 0.0 in each dict ,make sure all the dict has the same number of keys
'''
for i in setall:
    if i not in dictapr:dictapr[i]=0.0
    if i not in dictmay: dictmay[i] = 0.0
    if i not in dictjun: dictjun[i] = 0.0



