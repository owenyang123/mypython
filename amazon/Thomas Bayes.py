# some balls in box A,B.Box A has 70 reds,30 greens,Box B has 30 reds,70 greens

default_red=0.5
default_green=0.5
default_A=0.5
default_B=1-default_A
default_RA=0.7
default_GA=1-default_RA
default_RB=0.3
default_GB=1-default_RB

list1=[1,1,1,1,1,1,1,0,0,0,0,0]
list1.reverse()
print list1

def bayesfun(pIsBox1, pBox1, pBox2):
    return (pIsBox1 * pBox1)/((pIsBox1 * pBox1) + (1 - pIsBox1) * pBox2)

while (len(list1)>0):
    if list1[-1]==1:
        



