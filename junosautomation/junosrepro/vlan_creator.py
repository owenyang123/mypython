#vlan creator 
vlan = 6
while vlan < 5192:
	print 'set routing-instances vpls-gemstone-%s instance-type vpls' % (vlan)
	print 'set routing-instances vpls-gemstone-%s interface ae0.%s' % (vlan, vlan)
	print 'set routing-instances vpls-gemstone-%s route-distinguisher 3257:%s' % (vlan, vlan)
	print 'set routing-instances vpls-gemstone-%s vrf-target target:3257:%s' % (vlan, vlan)
	print 'set routing-instances vpls-gemstone-%s protocols vpls site-range 32' % (vlan)
	print 'set routing-instances vpls-gemstone-%s protocols vpls no-tunnel-services' % (vlan)
	print 'set routing-instances vpls-gemstone-%s protocols vpls site 3 site-identifier 3' % (vlan)
	print 'set interfaces ae0 unit %s encapsulation vlan-vpls' % (vlan)
	print 'set interfaces ae0 unit %s vlan-id %s' % (vlan, vlan)
	print 'set interfaces ae0 unit %s family vpls' % (vlan)
	vlan += 1