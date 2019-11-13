#!/usr/bin/env python

"""
E.Schornig
V1.0
Date: 16 October 2015
"""
#######################################################

HL2	= {'mgmt': '10.13.121.222',
	   'domain': 'TEF_WF'}

HL5 = {'mgmt': '10.13.121.225',
		'domain': 'TEF_WF'}

HL3_11  = {'Loopback': '1.1.3.11',
		   'PSN': '10.0.3.11', 
		   'mgmt': '10.13.121.210',
		   'domain': 'TEF_WF'}

HL3_12  = {'Loopback': '1.1.3.12',
		   'PSN': '10.0.3.12', 
		   'mgmt': '10.13.121.216',
		   'domain': 'TEF_WF'}

HL3_21  = {'Loopback': '1.1.3.21',
		   'PSN': '10.0.3.21', 
		   'mgmt': HL2['mgmt'],
		   'domain': 'TEF_WF'}

HL4_11  = {'Loopback': '1.1.4.11',
		   'PSN': '10.0.4.11', 
		   'mgmt': '10.13.121.219',
		   'domain': 'TEF_WF'}

HL4_12  = {'Loopback': '1.1.4.12',
		   'PSN': '10.0.4.12', 
		   'mgmt': '10.13.121.213',
		   'domain': 'TEF_WF'}

HL4_21  = {'Loopback': '1.1.4.21',
		   'PSN': '10.0.4.21', 
		   'mgmt': HL2['mgmt'],
		   'domain': 'TEF_WF'}

##############################################################

HL2_V	= {'mgmt': '10.92.37.105',
	   'domain': 'TEF_VMX'}

HL5_V = {'mgmt': '10.92.35.0',
		'domain': 'TEF_VMX'}

HL3_11_V  = {'Loopback': '1.1.3.11',
		   'PSN': '10.0.3.11', 
		   'mgmt': '10.92.37.208',
		   'domain': 'TEF_VMX'}

HL3_12_V  = {'Loopback': '1.1.3.12',
		   'PSN': '10.0.3.12', 
		   'mgmt': '10.92.37.205',
		   'domain': 'TEF_VMX'}

HL3_21_V  = {'Loopback': '1.1.3.21',
		   'PSN': '10.0.3.21', 
		   'mgmt': '10.92.37.105',
		   'domain': 'TEF_VMX'}

HL4_11_V  = {'Loopback': '1.1.4.11',
		   'PSN': '10.0.4.11', 
		   'mgmt': '10.92.37.188',
		   'domain': 'TEF_VMX'}

HL4_12_V  = {'Loopback': '1.1.4.12',
		   'PSN': '10.0.4.12', 
		   'mgmt': '10.92.37.108',
		   'domain': 'TEF_VMX'}

HL4_21_V  = {'Loopback': '1.1.4.21',
		   'PSN': '10.0.4.21', 
		   'mgmt': '10.92.37.105',
		   'domain': 'TEF_VMX'}

#############################################################

MX480_3  = {'Loopback': '192.168.200.9',
           'mgmt': '10.13.126.42',
           'vpls_check_template' : 'MX480_3_vpls.j2',
           'hostname' : 'MX480_3',
           'domain' : 'STC_WF'
            }

MX480_1  = {'Loopback': '192.168.200.4',
           'mgmt': '10.13.126.27',
           'hostname' : 'MX480_1',
           'domain' : 'STC_WF'
            }

T4000_1  = {'Loopback': '192.168.200.3',
           'mgmt': '10.13.126.23',
           'hostname' : 'T4000_1',
           'domain' : 'STC_WF'
            }

MX960_1  = {'Loopback': '192.168.200.1',
           'mgmt': '10.13.126.35',
           'vpls_check_template' : 'MX960_1_vpls.j2',
           'hostname' : 'MX960_1',
           'domain' : 'STC_WF'
            }

if __name__ == '__main__':
	pass
