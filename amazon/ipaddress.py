class Solution:
    def allipaddress(self, ipstr):
        list1=[]
        for i in range(0,3):
            if ipstr[i+1]!="0" and  int(ipstr[0:i+1])<256:
                temp1=ipstr[0:i+1]+"."
                layer1=ipstr[i+1:]
                for j in range(0,3):
                    if layer1[j+1]!="0" and int(layer1[0:j+1])<256:
                        temp2=layer1[0:j+1]+"."
                        layer2=layer1[j+1:]
                        for z in range(0,3):
                            if z+1<len(layer2) and layer2[z+1]!="0" and int(layer2[0:z+1])<256:
                                if int(layer2[z+1:])<256:
                                    temp3=layer2[0:z+1]+"."+layer2[z+1:]
                                    list1.append(temp1+temp2+temp3)
        return list1


k=Solution()
print k.allipaddress("1045894")
