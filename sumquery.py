import random
def generater_learned(t):
    sum1=[]
    sum2=[]
    if t<=1:
        print "nothing"
    else:
        for i in range(2,t+1):
            for k in range(1,i):
                s1=k
                s2=i-k
                sum2=[s1,s2,i]
                sum1.append(sum2)
    return sum1
maxnum_learned=int(input("input max number you learned:"))
numberofquery=int(input("input number you want:"))+1
sum=generater_learned(maxnum_learned)
for i in range(1,numberofquery):
    k=random.randint(0, len(sum)-1)
    a=sum[k][0]
    b=sum[k][1]
    c=sum[k][2]
    print str(a)+ '+'+str(b)+'='



