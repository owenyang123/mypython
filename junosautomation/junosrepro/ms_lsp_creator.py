# LSP creator
#  
lsp = 3001
while lsp != 5001:
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s apply-groups default_lsp_setup_tier1' % (lsp)		
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s apply-groups default_lsp_setup_tier2' % (lsp)	
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s to 207.46.64.223' % (lsp)	
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s metric 94998' % (lsp)
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s admin-group include-any transpacific' % (lsp)
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s admin-group include-any transarabia' % (lsp)
	print 'set protocols mpls label-switched-path TU.tya-96cbe-1a.lax-96cbe-1b.01-%s admin-group include-any transatlantic' % (lsp)
	lsp += 1




