import re
print(re.findall("e{8}",'aabbccddeeeeeeeeeeee'))
ip="8.7.34.2"
print(".".join(map(lambda x: str(int(x, 2)), re.findall(r'.{8}', "".join(bin(int(bte)).lstrip("0b").rjust(8, '0') for bte in ip.split('.'))[:21].ljust(32, '0')))))
print(int('10',2))