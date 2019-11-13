# LSP creator
#  
lsp = 9001
while lsp != 0:
	print 'set logical-systems JBRANTLEY protocols mpls label-switched-path TRANSIT-LSP%s'  % (lsp)
	print 'set logical-systems JBRANTLEY protocols mpls label-switched-path TRANSIT-LSP%s to 213.254.247.229' % (lsp)		
	lsp -= 1