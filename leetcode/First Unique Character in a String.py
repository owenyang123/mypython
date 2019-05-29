class Solution:
<<<<<<< HEAD
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

=======

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
>>>>>>> d95ec67a08eaac77d3858962c1ac4580db756ad7
