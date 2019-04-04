class Solution:
    """
    @param str: str: the given string
    @return: char: the first unique character in a given string
    """
    def firstUniqChar(self, str):
        if not str:
            return None
        dict1={}
        for i in range(len(str)):
            if str[i] not in dict1:
                dict1[str[i]]=1
            else:
                dict1[str[i]]+=1
        l=[]
        for i in dict1.keys():
            if dict1[i]==1:
                l.append(i)
        for i in str:
            if i in l:
                return i

        return None



k=Solution()
print k.firstUniqChar("aabc")

