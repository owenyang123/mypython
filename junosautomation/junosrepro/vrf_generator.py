# Ask for the number of VRFs to create 
#  
vrf = 98
while vrf != 2:
	if vrf >= 10:
		print 'set routing-instances HD1%s instance-type vrf' % (vrf)
		print 'set routing-instances HD1%s interface ge-5/0/8.1%s' % (vrf, vrf)
		print 'set routing-instances HD1%s route-distinguisher 2828:1%s'  % (vrf, vrf)
		print 'set routing-instances HD1%s vrf-target import target:2828:1%s' % (vrf, vrf)
		print 'set routing-instances HD1%s vrf-target export target:2828:1%s' % (vrf, vrf)
		print 'set routing-instances HD1%s vrf-table-label' % (vrf)
		print 'set routing-instances HD1%s protocols bgp group 1%s type external' % (vrf, vrf)
		print 'set routing-instances HD1%s protocols bgp group 1%s peer-as 1590%s' % (vrf, vrf, vrf)
		print 'set routing-instances HD1%s protocols bgp group 1%s neighbor %s.%s.%s.2' % (vrf, vrf, vrf, vrf, vrf)
		print 'set routing-instances HD1%s protocols bgp group 1%s peer-as 69%s' % (vrf, vrf, vrf)
		print 'set interfaces ge-5/0/8 unit 1%s vlan-id 1%s' % (vrf, vrf)
		print 'set interfaces ge-5/0/8 unit 1%s family inet address %s.%s.%s.1/30' % (vrf, vrf, vrf, vrf)
		print 'set policy-options community MCR2.MIN-HD1%s members target:2828:1%s' % (vrf, vrf)		
	else: 
		print 'set routing-instances HD10%s instance-type vrf' % (vrf)
		print 'set routing-instances HD10%s interface ge-5/0/8.10%s' % (vrf, vrf)
		print 'set routing-instances HD10%s route-distinguisher 2828:10%s'  % (vrf, vrf)
		print 'set routing-instances HD10%s vrf-target import target:2828:10%s' % (vrf, vrf)
		print 'set routing-instances HD10%s vrf-target export target:2828:10%s' % (vrf, vrf)
		print 'set routing-instances HD10%s vrf-table-label' % (vrf)
		print 'set routing-instances HD10%s protocols bgp group 10%s type external' % (vrf, vrf)
		print 'set routing-instances HD10%s protocols bgp group 10%s peer-as 1590%s' % (vrf, vrf, vrf)
		print 'set routing-instances HD10%s protocols bgp group 10%s neighbor %s.%s.%s.2' % (vrf, vrf, vrf, vrf, vrf)
		print 'set routing-instances HD10%s protocols bgp group 10%s peer-as 690%s' % (vrf, vrf, vrf)
		print 'set interfaces ge-5/0/8 unit 10%s vlan-id 10%s' % (vrf, vrf)
		print 'set interfaces ge-5/0/8 unit 10%s family inet address %s.%s.%s.1/30' % (vrf, vrf, vrf, vrf)
		print 'set policy-options community MCR2.MIN-HD10%s members target:2828:10%s' % (vrf, vrf)
	vrf -= 1