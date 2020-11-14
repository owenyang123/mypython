import turtle
import time
t=turtle.Pen()

for i in range(4):
    t.forward(100)
    t.left(90)
'''
for i in range(1000):
    t.forward(0.1)
    t.left(0.36)
'''

time.sleep(2)

def fibseq(n):
    if n==1 or n==0:return 1
    temp1,temp2=1,1
    for i in range(2,n+1):
        temp3=temp1+temp2
        temp1,temp2=temp2,temp3
    return temp3

print float(fibseq(10))/float(fibseq(9))