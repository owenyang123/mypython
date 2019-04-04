

for i in range(16001,20002):
    j=1000000+i
    print "set protocols mpls static-label-switched-path "+str(i)+"  transit "+str(j)+" swap "+str(j)+" next-hop 10.192.3.105"