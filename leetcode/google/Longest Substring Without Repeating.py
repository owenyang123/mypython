class Solution:
    """
    @param s: a string
    @return: an integer
    """
    def lengthOfLongestSubstring(self, s):
        # write your code here
        if not s:
            return 0
        seen = set([s[0]])
        i, j = 0, 0
        ret = 1
        while j < len(s) - 1:
            j += 1
            if s[j] not in seen:
                seen.add(s[j])
                ret = max(ret, j - i + 1)
            else:
                while s[i] != s[j]:
                    seen.remove(s[i])
                    i += 1
                i += 1
        return ret