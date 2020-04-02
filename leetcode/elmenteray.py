import sys
dict1={"1":31,"2":29,"3":31,"4":30,"5":31,"6":30,"7":31,"8":31,"9":30,"10":31,"11":30,"12":31}
def num2str(num):
    if num<10:return "0"+str(num)
    return str(num)
l=[]
for i in range(1,13):
    for j in range(1,32):
        if j>dict1[str(i)]:continue
        l.append(num2str(i)+num2str(j))

set1=set(l)
count=0
for i in  set1:
    if i[::-1] in set1:count+=1
print count

list1=[[1,2,3,4,5,6],[1,2,3,4,5,6],[1,2,3,4,5,6],[1,2,3,4,5,6]]

print map(list, zip(*list1))+list1

print   ['f'*(i%3==0)+'b'*(i%5==0)+str(i)*(i%3 !=0 and i%5!=0) for i in range(1,101) ]