class Solution(object):
    def longestCommonPrefix(self, strs):
        longes_str=""
        if not strs:
            return longes_str
        if len(strs)==1:
            return strs[0]
        strs.sort(key=lambda x:len(x))
        for i in range(len(strs[0])):
            if all([j.startswith(strs[0][0:i+1]) for j in strs[1:]]):
                longes_str= strs[0][0:i+1]
        return longes_str