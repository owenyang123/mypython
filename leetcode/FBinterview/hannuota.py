def hantower(n,start,end,mid):
    if n==1:
        print "move piece "+str(n)+" from "+start+" to "+end
        return
    hantower(n-1,start,mid,end)
    print "move piece " + str(n) + " from "+ start +" to " + end
    hantower(n-1,mid,end,start)

hantower(3,"A","C","B")
def anotherway(n,a,b,c):
    if n == 1:
        print(a, '-->', c)
        return
    move(n - 1, a, c, b)
    print(a, '-->', c)
    move(n - 1, b, a, c)
