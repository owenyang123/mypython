import time
start_time = time.time()
class Solution:
    def restoreIpAddresses(self, s):
        if not s or len(s) <= 1:
            return []
        ipstr = s
        list1 = []
        if len(ipstr) < 4 or len(ipstr) > 12 or not ipstr:
            return []
        for i in range(0, 3):
            if self.helper(ipstr[0:i + 1]) :
                temp1 = ipstr[0:i + 1] + "."
                layer1 = ipstr[i + 1:]
                for j in range(0, 3):
                    if j < len(layer1) - 1 and self.helper(layer1[0:j + 1]):
                        temp2 = layer1[0:j + 1] + "."
                        layer2 = layer1[j + 1:]
                        for z in range(0, 3):
                            if z < len(layer2) - 1 and self.helper(layer2[0:z + 1]) and self.helper(layer2[z + 1:]):
                                temp3 = layer2[0:z + 1] + "." + layer2[z + 1:]
                                list1.append(temp1 + temp2 + temp3)
        return list1
    def helper(self, str1):
        if len(str1) == 1:
            return True
        if int(str1) > 255:
            return False
        if str1[0] != "0":
            return True
        return False
k=Solution()
print k.restoreIpAddresses("111111111")
print("--- %s seconds ---" % (time.time() - start_time))

start_time = time.time()
class Solution1:
    def restoreIpAddresses(self, s):
        res=[]
        for i in [1,2,3]:
            for j in [i+1,i+2,i+3]:
                for k in [j+1,j+2,j+3]:
                    if k>=len(s):
                        break
                    s1,s2,s3,s4=s[:i],s[i:j],s[j:k],s[k:]
                    add_ip = True
                    for st in [s1,s2,s3,s4]:
                        if (st!="0" and st[0]=="0") or int(st)>255:
                            add_ip=False
                            break
                    if add_ip: res.append(s1+"."+s2+"."+s3+"."+s4)
        return res

k=Solution1()
print k.restoreIpAddresses("111111111")
print("--- %s seconds ---" % (time.time() - start_time))


class Solution(object):
    def validIPAddress(self, IP):
        def isIPv4(s):
            if not s:return False
            try:
                if str(int(s)) == s and 0 <= int(s) <= 255:return True
                return False
            except:
                return False
        def isIPv6(s):
            if not s:return False
            try:
                if len(s) <= 4 and int(s, 16) >= 0:return True
                return False
            except:
                return False
        if IP.count(".") == 3 and all(isIPv4(i) for i in IP.split(".")):
            return "IPv4"
        if IP.count(":") == 7 and all(isIPv6(i) for i in IP.split(":")):
            return "IPv6"
        return "Neither"


import re

pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
test = pat.match(hostIP)
if test:
   print "Acceptable ip address"
else:
   print "Unacceptable ip address"