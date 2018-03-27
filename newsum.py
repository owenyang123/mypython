import random
import scipy.special as cp
def generater_learned(x,t):
    sum1=[]
    sum2=[]
    if t<=1:
        print "nothing"
    else:
        for i in range(x,t+1):
                sum1.append(i)
    return sum1
maxnum_learned=int(input("input max number you learned:"))
numberofmin=int(input("input min number you leraned should be >= 2,but <=the max number you just input:"))
sum=generater_learned(numberofmin,maxnum_learned-1)
k1=maxnum_learned-numberofmin
k1=int(cp.comb(k1,2))
print "max value is "+str(k1)+" for next input"
numberofquery=int(input("input number you want:"))
if sum:
    count=0
    while(count<=numberofquery-1):
        twonumber=[]
        for i in random.sample(sum,2):
            twonumber.append(i)
        a=twonumber[0]
        b=twonumber[1]
        print str(a)+"+"+str(b)+"="
        count=count+1
if sum:
    count=0
    while(count<=numberofquery-1):
        twonumber=[]
        for i in random.sample(sum,2):
            twonumber.append(i)
        a=twonumber[0]
        b=twonumber[1]
        if a>b:
            print str(a)+"-"+str(b)+"="
        else:
            print str(b)+"-"+str(a)+"="
        count=count+1
