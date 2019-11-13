#!/usr/bin/python
from jnpr.junos import Device
import re
import os
import sys
import argparse
import time
import warnings
import threading
from lxml import etree
from xml.dom.minidom import parse, parseString
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
import datetime

def onlinefpcs(dev):
    # Input: Dev Pointer
    # Output: Array of FPC sloat which are online 
    fpc_lxml_elements = dev.rpc.get_fpc_information()
    string_fpc = etree.tostring(fpc_lxml_elements)
    dom_fpc = parseString(string_fpc)
    cms = dom_fpc.getElementsByTagName("fpc")
    print 'Number of FPCs Sloat', len(cms)
    fpcsloat = []
    for cm in cms:
        state = str(cm.getElementsByTagName("state")[0].firstChild.data)
        fpcsn = cm.getElementsByTagName("slot")[0].firstChild.data
        fpc = re.match(r"Online", state)
        if fpc:
            fpcsloat.append(str(fpcsn))
    return fpcsloat

def testunilistlb(dev,onlinefpcs,unilistnh,LBfile):
	lbshowfile = open(LBfile,'w')
	for onlinefpc in onlinefpcs:
		lbtestadd = dev.rpc.request_pfe_execute(target='fpc'+onlinefpc,command='test nhdb unilist load-balance add-counters %s' %(unilistnh))
		print lbtestadd.text
		lbshowfile.write(lbtestadd.text)
		print "We are waiting for 1 second"
		time.sleep(1)
		lboutput = dev.rpc.request_pfe_execute(target='fpc'+onlinefpc,command='show nhdb lb unilist-counters')
		lbshow = lboutput.text
		print lbshow
		lbshowfile.write(lbshow)
		processlboutput(lbshow,lbshowfile)
		lbtestdel = dev.rpc.request_pfe_execute(target='fpc'+onlinefpc,command='test nhdb unilist load-balance delete-counters  %s' %(unilistnh))
		print lbtestdel.text
		lbshowfile.write(lbtestdel.text)
	lbshowfile.close()
def processlboutput(lbshow,lbshowfile):
	print lbshow
	unilistid = ""
	pfes = []
	stats = []
	lbshow = lbshow.split('\n')
	for line in xrange(len(lbshow)):
		if "GOT:  " in lbshow[line]:
			lbshow[line] = lbshow[line].replace("GOT:  "," ")
	for line in lbshow:
		if "Nexthop id :" in line:
			unilistid = filter(str.isdigit, line)
		if "PFE " in line:
			pfe = filter(str.isdigit, line)
			int(pfe)
			pfes.append(pfe)
		if re.match("^[0-9 ]+$", line):
			stats.append(pfe)
			for string in line.split():
				if string.isdigit():
					stats.append(string)
	nhstats = []
	n = 6
	nhidperpfe = []
	for stat in xrange(0, len(stats), n):
		nhstats = stats[stat:stat+n]
		nhidperpfe.append(nhstats)
	m = len(pfes)
	#Find NHIDs and total Packet Rate
	totalpktrate = []
	totalbyterate = []
	for pfe in pfes:
		totpkt = 0;
		totbyte = 0;
		for nhidrate in nhidperpfe:
			if nhidrate[0] == pfe:
				totpkt += int(nhidrate[3])
				totbyte += int(nhidrate[5])
		if totpkt == 0: 
			totpkt = 1 #to avoid divide by zero
		if totbyte == 0:
			totbyte = 1 #to avoid divide by zero
		totalpktrate.append(totpkt)
		totalbyterate.append(totbyte)
	#Take Percentage with each nhid
	lbnhidpktrate = []
	lbnhid = []
	lbpfe = []
	lbnhidbyterate = []
	lbnhidpkt = []
	lbnhidbyte = []
	nhidpktper = []	
	i = 0
	for pfe in pfes:
	
		for nhidrate in nhidperpfe:
			if nhidrate[0] == pfe:
				lbnhidpktrate.append(round((int(nhidrate[3])*100.00)/totalpktrate[i],1))
				lbnhidpkt.append(nhidrate[3])
				lbnhid.append(nhidrate[1])
				lbpfe.append(nhidrate[0])
				lbnhidbyterate.append(round((int(nhidrate[5])*100.00)/totalbyterate[i],1))
				lbnhidbyte.append(nhidrate[5]) 
		i+=1
	for lb in xrange(len(lbnhid)):
		print "PFE %s	, NHID %s	, PKTrate %s	, Percentage of PKTrate %s	, Byterate %s	, Percentage of Byterate %s		" % (lbpfe[lb],lbnhid[lb],lbnhidpkt[lb],lbnhidpktrate[lb],lbnhidbyte[lb],lbnhidbyterate[lb])
		lbshowfile.write("PFE %s	, NHID %s	, PKTrate %s	, Percentage of PKTrate %s	, Byterate %s	, Percentage of Byterate %s		,\n" % (lbpfe[lb],lbnhid[lb],lbnhidpkt[lb],lbnhidpktrate[lb],lbnhidbyte[lb],lbnhidbyterate[lb]))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Enter Device information")
	parser.add_argument('-f', action='store',dest='LBfile', help="Enter File Name for LB")
	parser.add_argument('-a', action='store',dest='Address', help="Enter IP Address for device to monitor")
	parser.add_argument('-u', action='store',dest='unilistnh', help="Enter Unilist NHDB ID to monitor")
	result = parser.parse_args()
	print "IP Address %s" % (result.Address)
	dev = Device(host=result.Address, user="labroot", passwd="lab123")
	dev.open()
	onlinefpcs = onlinefpcs(dev)
	print onlinefpcs
	testunilistlb(dev,onlinefpcs,result.unilistnh,result.LBfile)
	

	
			
					

		
			
				
			
		

			
	