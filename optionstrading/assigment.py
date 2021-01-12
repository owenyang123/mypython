import basictools as bt
import random
import copy
import csv
parent_list=["Gavin","Owen","Chao","Maggie","Vivian","Nina"]
child_list=["Angelina","Audrey","Nora","Ethan","Edwin","Annie"]
arrange_list=[]
n=0
while (n<=9):
    temp = copy.deepcopy(child_list)
    for i in range(len(parent_list)):
        index_k=random.randint(0, len(temp)-1)
        loop=0
        while (i==child_list.index(temp[index_k])):
            index_k = random.randint(0, len(temp)-1)
            loop+=1
            if loop==5:break
        if loop==5:
            for _ in range(1,len(parent_list)):
                arrange_list.pop()
        else:
            arrange_list.append((parent_list[i],temp[index_k],str(bt.get_data(-4-n*7)),"Week "+str(n+11)))
            temp.pop(index_k)
    if loop==5:pass
    else:n+=1
with open("arrangement.csv", 'a') as fd:
    for t in arrange_list:
        print t
        writer = csv.writer(fd)
        writer.writerow(list(t))
