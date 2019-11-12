import socket, struct

# Convert a hex to IP
def hex2ip(hex_ip):
    addr_long = int(hex_ip,16)
    hex(addr_long)
    hex_ip = socket.inet_ntoa(struct.pack(">L", addr_long))
    return hex_ip

# Convert IP to bin
def ip2bin(ip):
    ip1 = '.'.join([bin(int(x)+256)[3:] for x in ip.split('.')])
    return ip1

# Convert IP to hex
def ip2hex(ip):
    ip1 = ''.join([hex(int(x)+256)[3:] for x in ip.split('.')])
    return ip1

#print hex2ip("c0a80100")
#print ip2bin("192.168.1.0")
#print ip2hex("192.168.1.0")

ip = raw_input('Enter IP or IP in hex:\n')
convert = raw_input("Enter conversion method: [b - ip to binary], [h - hex to ip], [i - ip from hex]:\n") 

if (convert == "b"): 
	print "\nIP " + ip + " is " + ip2bin(ip) + " in binary.\n" 
elif (convert == "h"):
	print "\nHex value " + ip + " is " + hex2ip(ip) + " in hex.\n" 
elif (convert == "i"): 
	print "\nIP " + ip + " is " + ip2hex(ip) + " in hex.\n" 
else: 
	print "Invalid selection - aborting."

	
		