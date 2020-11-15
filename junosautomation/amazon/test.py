'''
l=[0, 1, 7, 2, 0, 0, 0, 0, 0, 0]
def allin1(l):
    if sum(l)!=len(l):return False
    if l==[0,2] or l==[2,0]:return 1
    if len([1 for i in l if i==1])==len(l):return 0
    else:
        temp=[True if sum(l[0:i+1])==len(l[0:i+1]) else False for i in range(len(l))]
        if temp.count(True)>=2:
            for i in range(len(temp)):
                if temp[i]:return allin1(l[0:i+1])+allin1(l[i+1:])
        else:
            #if l[0]==1:return allin1(l[1:])
            if l[0]==0:
                for i in range(len(l)):
                    if l[i]>1:
                        l[i]-=1
                        return i+allin1(l[1:])
            return l[0]-1+allin1([l[1]+l[0]-1]+l[2:])
def set_plate(plates):
    res, s = [], 0
    for i, p in enumerate(plates):
        s += p
        res.append(i + 1 - s)
    return sum(abs(r) for r in res)
print set_plate(l)
print allin1(l)
'''
def validcheck(list1,str1):
    if not list1:return "empty"
    temp=[1 for i in list1 if i==int(str1)]
    return "done" if len(temp)==len(list1) else"yet"
dict1={'0':[0,1,2],"1":[2,1,0],"2":[1,1,0]}
def movestone(dcit1,k):
    current=[validcheck(dcit1[i],i) for i in sorted(dict1.keys())]
    if "yet" not in current:return
    for i in range(k):
        if current[i]=="done":
            dict1[str(i)]=[]
            temp=i
            break
        elif current[i]=="empty":
            temp=i
            break
        temp=-1
    for i in range(k):
        if current[i]=="yet":
            while (validcheck(dcit1[str(i)],str(i))=="yet"):
                if temp==-1:
                    temp1,ton=dict1[str(i)].pop(),i%k+1
                    if ton==3:ton=0
                    print "form line "+str(i)+" to line " +str(ton)
                else:
                    temp1, ton = dict1[str(i)].pop(), temp
                    print "form line " + str(i) + " to line " + str(ton)
                dict1[str(ton)].append(temp1)
        temp3=i
        break
    current = [validcheck(dcit1[i], i) for i in sorted(dict1.keys())]
    for i in range(k):
        if i==temp3:continue
        temp4=[]
        while (validcheck(dcit1[str(i)],str(i))=="yet"):
            print current
            break




    return
print movestone(dict1,3)










