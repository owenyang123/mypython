import string,random
cap=""
words=".".join((string.ascii_letters,string.digits))
print words
for i in range(8):
    cap+=random.choice(words)
    #print cap

def findex(A):
    if A==0 or A==1:return 1
    if A==2:return 2
    temp0=1
    temp1=2
    temp2=3
    for i in range(3,A+1):
        temp2=temp0+temp1
        temp0,temp1=temp1,temp2
    return temp2
print findex(100)