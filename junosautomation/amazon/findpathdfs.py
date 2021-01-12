class SR_input():
    def findpath(self,topology,start,end):
        if not topology:return []
        if start==end:return [[end]]
        self.path=[]
        self.dfsroute(topology,end,[start])
        return self.path
    def dfsroute(self,topology,end,temppath):
        if end==temppath[-1]:
            self.path.append(temppath)
            return
        for i in topology[temppath[-1]]:
            if i in set(temppath):continue
            self.dfsroute(topology, end, temppath+[i])
    def bwalloc(self,total, weight_list):
        lenth = len(weight_list)
        sumweight = sum(weight_list)
        leftbw = total % sumweight
        list1 = [0] * lenth
        for i in range(lenth):
            list1[i] = weight_list[i] * (total / sumweight)
            list1[i] += min(leftbw, weight_list[i])
            leftbw -= min(leftbw, weight_list[i])
        return list1, sum(list1)

test=SR_input()
topology={1:[2,3,4],2:[1,3,5],3:[1,2,4,5],4:[1,3,5],5:[2,3,4,6],6:[5]}

print sorted(test.findpath(topology,1,6),key=lambda x:len(x))
print test.bwalloc(927,sorted([2,2,2,1,3,3,3,4,8]))

'''
mport time
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
'''