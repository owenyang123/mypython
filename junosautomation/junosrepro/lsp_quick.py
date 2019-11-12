#vlan creator 
vlan = 1
while vlan < 256:
	print 'set protocols mpls label-switched-path BREAK-TT%s to 4.4.4.%s' % (vlan, vlan)
	vlan += 1
	
