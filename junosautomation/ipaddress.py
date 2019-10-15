class Solution:
    def allipaddress(self, ipstr):
        list1=[]
        for i in range(0,3):
            if ipstr[i+1]!="0" and  int(ipstr[0:i+1])<256:
                temp1=ipstr[0:i+1]+"."
                layer1=ipstr[i+1:]
                for j in range(0,3):

                    if j<len(layer1)-1 and layer1[j+1]!="0" and int(layer1[0:j+1])<256:
=======
                    if layer1[j+1]!="0" and int(layer1[0:j+1])<256 :

                        temp2=layer1[0:j+1]+"."
                        layer2=layer1[j+1:]
                        for z in range(0,3):
                            if z+1<len(layer2) and layer2[z+1]!="0" and int(layer2[0:z+1])<256:
                                if int(layer2[z+1:])<256:
                                    temp3=layer2[0:z+1]+"."+layer2[z+1:]
                                    list1.append(temp1+temp2+temp3)
        return list1


k=Solution()
<<<<<<< HEAD

print k.allipaddress("111123")





=======
print k.allipaddress("11223344")
>>>>>>> d3685ee5740768bdfb35d6216b9b63f7d7664960

class solutions1:
    def ipadd(self,ipstr):
        if len(ipstr)>12 or len(ipstr)<4:
            return None
        coms=[]
        self.dfs(ipstr,"",coms)
        return coms
    def dfs(self,ipstr,tempstr,coms):
        if tempstr.count(".")==3:
            if ipstr!="" and int(ipstr)<256:
                coms.append(tempstr+ipstr)
            return
        else:
            for i in range(1,4):
                if i<len(ipstr) and int(ipstr[0:i])<256 and ipstr[i]!="0":
                    self.dfs(ipstr[i:],tempstr+ipstr[0:i]+".",coms)

k=solutions1()
print k.ipadd("111123")



class Solution2:
    def trailingZeros(self, n):
        number5=0
        while(n!=0):
            n=n/5
            number5=number5+n
        return number5

x=Solution2()
print x.trailingZeros(100)
=======
                if i<=len(ipstr ) and int(ipstr[0:i])<256 and ipstr[i]!="0":
                    self.dfs(ipstr[i:],tempstr+ipstr[0:i]+".",coms)

k=solutions1()
print k.ipadd("11223344")




>>>>>>> d3685ee5740768bdfb35d6216b9b63f7d7664960


