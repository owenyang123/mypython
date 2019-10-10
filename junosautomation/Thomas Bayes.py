# some balls in box A,B.Box A has 70 reds,30 greens,Box B has 30 reds,70 greens
default_red=0.5
default_green=0.5
default_A=0.5
default_B=1-default_A
default_RA=0.7
default_GA=1-default_RA
default_RB=0.3
default_GB=1-default_RB

list1=[0,0,0,0,1,1,1,1,1,1,1,1]


#a:default_RA,b:default_RB,c:default_A,d:default_B
def bayesfun(a,b,c,d):
    return (a * c)/((a * c) + (b* d))

while (len(list1)>0):
    if list1[-1]==1:
        default_A=bayesfun(default_RA,default_RB,default_A,default_B)
        default_B=1-default_A
        print default_A
        list1.pop()
    else:
        default_A=bayesfun(default_GA,default_GB,default_A,default_B)
        default_B=1-default_A
        print default_A
        list1.pop()
        



