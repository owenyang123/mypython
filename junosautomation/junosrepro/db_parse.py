#!/usr/bin/python
import re
import string


#fp = open('isis_db.log','r').read()
fp = open('full_isis_db.log','r').read()

total_lsp = 0
total_srnbr = 0
total_rsvpnbr = 0
total_risknbr = 0
total_isnbrs = 0
total_rsnosr = 0
total_srnors_node = 0
total_sr_node = 0
max_nbrc = 0

lsps = fp.split("transmissions")
for lsp in lsps:
    print '######################################'
    lsp1 = lsp.split(", Checksum: ")
    if (lsp1.__len__() == 2):
	lsp = lsp1[0].split()
	if lsp:
	    lspname = lsp[0]
	    print 'Name: '+lspname
	    tmp_risknbr = total_risknbr
	    total_lsp = total_lsp + 1
	    tlvs = lsp1[1].split("TLVs:")
	    node_has_sr = 0
	    if tlvs:
		nbrc = tlvs[1].count("IS extended neighbor:")
		isnbrs = tlvs[1].split("IS extended neighbor:")
		tlv_tot_len = 0
		tlv_strt_nbr = 0
		ex_tlv = 0
		if (nbrc > 0):
		    #print nbrc
		    if (nbrc > max_nbrc):
			max_nbrc = nbrc
		    total_len = 0
		    nbr_no = 0
		    has_sr = 0
		    has_rs = 0
		    dnbr = [0] * 12
		    for nbr in isnbrs:
			if re.search('Metric',nbr):
			    curtot_len = total_len
			    nbr_len = 11
			    total_isnbrs = total_isnbrs + 1
			    nbr_no = nbr_no + 1
			    nbrn = nbr.split()
			    # SUBTLV LEN
			    if re.search('Local interface index:',nbr):
				nbr_len = nbr_len + 10
			    if re.search('Maximum bandwidth:',nbr):
				nbr_len = nbr_len + 6
			    if re.search('Maximum reservable bandwidth:',nbr):
				nbr_len = nbr_len + 6
			    if re.search('Current reservable bandwidth:',nbr):
				nbr_len = nbr_len + 34
			    if re.search('IP address:',nbr):
				nbr_len = nbr_len + 6
			    if re.search("Neighbor's IP address:",nbr):
				nbr_len = nbr_len + 6
			    if re.search('Traffic engineering metric:',nbr):
				nbr_len = nbr_len + 5
			    if re.search('Administrative groups:',nbr):
				nbr_len = nbr_len + 6
			    if re.search('P2P IPV4 Adj-SID -',nbr):
				nbr_len = nbr_len + 7
			    if re.search('P2P IPV6 Adj-SID -',nbr):
				nbr_len = nbr_len + 7
			    if re.search('LAN IPV4 Adj-SID -',nbr):
				nbr_len = nbr_len + 13
			    if re.search('LAN IPV6 Adj-SID -',nbr):
				nbr_len = nbr_len + 13
			    if re.search('Unknown sub-TLV type 252, length 32',nbr):
				nbr_len = nbr_len + 34
			    if re.search('Bandwidth model:',nbr):
				nbr_len = nbr_len + 35
			    total_len = total_len + nbr_len
			    tlv_tot_len = tlv_tot_len + nbr_len
			    if (tlv_tot_len > 254):
				ex_tlv = ex_tlv + 1
				tlv_tot_len = nbr_len
				tlv_strt_nbr = nbr_no
			    print nbr_no,'IS nbr: '+nbrn[0]+', Length:',nbr_len,'total (',total_len,')' 
			    # SUBTLV LEN
			    if re.search('bandwidth',nbr):
				#print '  has rsvp'
				has_rs = has_rs + 1
				if re.search('Adj-SID',nbr) is None:
				    total_rsnosr = total_rsnosr + 1
			    if re.search('bandwidth',nbr) is None:
				if (has_sr == 0):
				    if ((total_len + (nbr_no*14)) > 254):
					if ((total_len + (nbr_no*14)) < 270):
					    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if SR enabled on all IS nbrs'
				    if (nbr_no > tlv_strt_nbr):
					if ((total_len + ((nbr_no - tlv_strt_nbr)*14)) > 254):
					    if ((total_len + ((nbr_no - tlv_strt_nbr)*14)) < 270):
						print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if SR enabled on all IS nbrs'
			    if re.search('Adj-SID',nbr):
				#print '  has SR'
				node_has_sr = 1
				has_sr = has_sr + 1
				if re.search('bandwidth',nbr) is None:
				    #print 'LSP: '+lspname+' nbr: '+nbrn[0]+'  SR but no RSVP'
				    dbg_print = 1
				    if ((total_len - 10) > 254):
					if ((total_len - 10) < 270):
					    dbg_print = 0
					    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if earlier IS Nbr misses a subtlv'
				    if ((total_len ) > 254):
					if ((total_len ) < 270):
					    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk '
					    dbg_print = 0
				    if (has_sr > 1):
					if ((total_len - ((has_sr - 1)*14) ) > 254):
					    if ((total_len - ((has_sr - 1)*14)) < 270):
						print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if SR removed from previous links'
						dbg_print = 0
				    if (nbr_no > 2):
					if ((total_len - 20) > 254):
					    if ((total_len - 20) < 270):
						print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At minor risk if 2 earlier IS Nbrs misses a subtlv'
						dbg_print = 0
				    if (nbr_no > 3):
					if ((total_len - 30) > 254):
					    if ((total_len - 30) < 270):
						print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At very minor risk if 3 earlier IS Nbrs misses a subtlv'
						dbg_print = 0
					for i in range(0,(nbr_no-2)):
					    if ((total_len - dnbr[i]) > 254):
						if ((total_len - dnbr[i]) < 270):
						    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if IS Nbr',i,' gets removed'
						    dbg_print = 0
				    if (nbr_no > 4):
					if ((total_len - 40) > 254):
					    if ((total_len - 40) < 270):
						print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At very minor risk if 4 earlier IS Nbrs misses a subtlv each'
						dbg_print = 0
					for i in range(0,(nbr_no-2)):
					    for j in range(0,(nbr_no-2)):
						if (i <> j):
						    if ((total_len - (dnbr[i] + dnbr[j])) > 254):
							if ((total_len - (dnbr[i] + dnbr[j])) < 270):
							    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At minor risk if IS Nbr',i,'and',j,' gets removed'
							    dbg_print = 0
				    # tlv_tot_len
				    if ((tlv_tot_len - 10) > 254):
					if ((tlv_tot_len - 10) < 270):
					    dbg_print = 0
					    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if earlier IS Nbr misses a subtlv'+' in TLV 22 occurance',ex_tlv
				    if ((tlv_tot_len ) > 254):
					if ((tlv_tot_len ) < 270):
					    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk '+' in TLV 22 occurance',ex_tlv
					    dbg_print = 0
				    if (has_sr > 1):
					if ((tlv_tot_len - ((has_sr - 1)*14) ) > 254):
					    if ((tlv_tot_len - ((has_sr - 1)*14)) < 270):
						print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if SR removed from previous links'+' in TLV 22 occurance',ex_tlv
						dbg_print = 0
				    if (nbr_no > tlv_strt_nbr):
					if ((nbr_no - tlv_strt_nbr) > 2):
					    if ((tlv_tot_len - 20) > 254):
						if ((tlv_tot_len - 20) < 270):
						    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At minor risk if 2 earlier IS Nbrs misses a subtlv'+' in TLV 22 occurance',ex_tlv
						    dbg_print = 0
					if ((nbr_no - tlv_strt_nbr) > 3):
					    if ((tlv_tot_len - 30) > 254):
						if ((tlv_tot_len - 30) < 270):
						    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At very minor risk if 3 earlier IS Nbrs misses a subtlv'+' in TLV 22 occurance',ex_tlv
						    dbg_print = 0
					    for i in range(0,((nbr_no - tlv_strt_nbr)-2)):
						if ((tlv_tot_len - dnbr[i]) > 254):
						    if ((tlv_tot_len - dnbr[i]) < 270):
							print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At risk if IS Nbr',i,' gets removed'+' in TLV 22 occurance',ex_tlv
							dbg_print = 0
					if ((nbr_no - tlv_strt_nbr) > 4):
					    if ((tlv_tot_len - 40) > 254):
						if ((tlv_tot_len - 40) < 270):
						    print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At very minor risk if 4 earlier IS Nbrs misses a subtlv each'+' in TLV 22 occurance',ex_tlv
						    dbg_print = 0
					    for i in range(0,((nbr_no - tlv_strt_nbr)-2)):
						for j in range(0,((nbr_no - tlv_strt_nbr)-2)):
						    if (i <> j):
							if ((tlv_tot_len - (dnbr[i] + dnbr[j])) > 254):
							    if ((tlv_tot_len - (dnbr[i] + dnbr[j])) < 270):
								print 'LSP: '+lspname+' nbr:'+nbrn[0]+'  At minor risk if IS Nbr',i,'and',j,' gets removed'+' in TLV 22 occurance',ex_tlv
								dbg_print = 0
				    total_risknbr = total_risknbr + 1
				    if (dbg_print == 1):
					print 'LSP: '+lspname+' nbr: '+nbrn[0]+'  SR but no RSVP'
			    dnbr[nbr_no - 1] = nbr_len
		    total_rsvpnbr = total_rsvpnbr + has_rs
		    total_srnbr = total_srnbr + has_sr
		    print 'IS Nbr length array:',dnbr
	    if (total_risknbr > tmp_risknbr):
		total_srnors_node = total_srnors_node + 1
	    if (node_has_sr == 1):
		total_sr_node = total_sr_node + 1
print 'Summary'
print 'total LSPs:',total_lsp
print 'total IS Nbrs across all LSPs:',total_isnbrs
print 'total isnbr with rsvp:',total_rsvpnbr
print 'total isnbr with sr:',total_srnbr
print 'total isnbr with sr but no rsvp:',total_risknbr
print 'total isnbr with rsvp but no sr:',total_rsnosr
print 'total LSPs with sr:',total_sr_node
print 'total LSPs with sr but no rsvp isnbr:',total_srnors_node
print 'Max nbr count in an LSP:',max_nbrc

