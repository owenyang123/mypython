def hantower(n,start,end,mid):
    if n==1:
        print "move piece "+str(n)+" from "+start+" to "+end
        return
    hantower(n-1,start,mid,end)
    print "move piece " + str(n) + " from "+ start +" to " + end
    hantower(n-1,mid,end,start)

hantower(10,"A","C","B")