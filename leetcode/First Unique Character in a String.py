class Solution:

    def firstUniqChar(self, str):
        if not str:
            return None
        if len(str)==1:
            return str[0]
        i=0
        j=0
        for i in range(len(str)):
            for j in range(len(str)):
                if str[i]==str[j] and i!=j:
                    break
                if j==len(str)-1:
                    return str[i]

k=Solution()
print k.firstUniqChar("abcdefgba")
