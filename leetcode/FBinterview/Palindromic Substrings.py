class Solution:

    def countPalindromicSubstrings(self, str):
        if not str:
            return 0
        if len(str)==1:
            return 1
        lenth=len(str)
        count=0
        for i in range(lenth):
            for j in range(i+1.lenth+1):
                if self.checkPalindromic(str[i:j]):
                    count+=1
        return count
    def checkPalindromic(self,str123):
        if len(str123)==1:
            return True
        i=0
        j=len(str1)-1
        while(i<j):
            if str123[i]!=str123[j]:
                return False
            i+=1
            j-=1
        return True