

def fibseq(n):
    if n==1 or n==0:return 1
    temp1,temp2=1,1
    for i in range(2,n+1):
        temp3=temp1+temp2
        temp1,temp2=temp2,temp3
    return temp3

for i in range(100):
    print fibseq(i)

print float(354224848179261915075)/float(218922995834555169026)