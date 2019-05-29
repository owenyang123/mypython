class Solution:

    def compress(self, originalString):
        if not originalString:
            return ""
        if len(originalString)==1:
            return originalString
        str1=""
        count=1
        i=0
        j=1
        while (i<=len(originalString)-1 and j<=len(originalString)-1 ):
            if j==len(originalString)-1 and originalString[i]==originalString[j]:
                str1 = str1 + str(originalString[i]) + str(count+1)
            if j == len(originalString) - 1 and originalString[i] != originalString[j]:
                str1 = str1 + str(originalString[i]) + str(count)+str(originalString[j])+"1"
            if originalString[i]==originalString[j]:
                j=j+1
                count=count+1
            else :
                str1=str1+str(originalString[i])+str(count)
                count=1
                i=j
                j=i+1
        if originalString[len(originalString)-1]!=originalString[len(originalString)-2]:
            if len(originalString)<=len(str1[0:len(str1)-2]):
                return originalString
            else:
                return str1[0:len(str1)-2]
        if originalString[len(originalString)-1]==originalString[len(originalString)-2]:
            if len(originalString)<=len(str1[0:len(str1)]):
                return originalString
            else:
                return str1

k=Solution()

print k.compress("aabcccccaaaq")

