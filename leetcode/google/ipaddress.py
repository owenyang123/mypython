class Solution:

    def restoreIpAddresses(self, s):
        if not s or len(s) <= 1:
            return []
        ipstr = s
        list1 = []
        if len(ipstr) < 4 or len(ipstr) > 12 or not ipstr:
            return []
        for i in range(0, 3):
            if self.helper(ipstr[0:i + 1]) and int(ipstr[0:i + 1]) < 256:
                temp1 = ipstr[0:i + 1] + "."
                layer1 = ipstr[i + 1:]
                for j in range(0, 3):
                    if j < len(layer1) - 1 and int(layer1[0:j + 1]) < 256 and self.helper(layer1[0:j + 1]):
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




