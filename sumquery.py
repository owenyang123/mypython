import random

def generater_learned(x,t):
    sum1=[]
    sum2=[]
    if t<=1:
        print "nothing"
    else:
        for i in range(x,t+1):
            for k in range(1,int(i/2)+1):
                s1=k
                s2=i-k
                sum2=[s1,s2,i]
                sum1.append(sum2)
    return sum1

def today_learned(t):
    sum1=[]
    sum2=[]
    if t<=1:
        print "nothing"
        return
    else:
            for k in range(1,int(t/2)+1):
                s1=k
                s2=t-k
                sum2=[s1,s2,t]
                sum1.append(sum2)
    return sum1

maxnum_learned=int(input("input max number you learned:"))
numberofmin=int(input("input min number you leraned should be >= 2:"))
sum=generater_learned(numberofmin,maxnum_learned-1)
k1=str(len(sum))
print "max value is "+k1+" for next input"
numberofquery=int(input("input number you want:"))

numberofquery=numberofquery+2
lensum=int(len(sum))

sum1=today_learned(maxnum_learned)
lensum1=int(len(sum1))
rsum=[]
if sum:
    for i in random.sample(range(1,lensum),numberofquery-1):
        a=sum[i][0]
        b=sum[i][1]
        c=sum[i][2]
        rsum.append([a,b,c])


if rsum:
    for i in random.sample(range(1,len(rsum)),len(rsum)-1):
        print str(rsum[i][0])+'+'+str(rsum[i][1])+'='+' '
        #print '  '+'-'+str(rsum[i][0])+'='+str(rsum[i][1])
if rsum:
    for i in random.sample(range(1,len(rsum)),len(rsum)-1):
        print str(rsum[i][2])+'-'+str(rsum[i][1])+'='+' '

print random.sample(1,10)