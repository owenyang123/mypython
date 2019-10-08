class Solution:
    def validPalindrome(self, s):
        if self.isPalindrome(s):
            return True

        for i in range(len(s) / 2):
            j = len(s) - 1 - i
            if s[j] != s[i]:
                s1 = s.replace(s[i], "")
                s2 = s.replace(s[j], "")
                if self.isPalindrome(s1) or self.isPalindrome(s2):
                    return True
                else:
                    return False
        return False

    def isPalindrome(self, s):
        # write your code here

        l, r = 0, len(s) - 1
        s = s.lower()
        while l < r:
            while l < r and not s[l].isalnum:
                l += 1
            while l < r and not s[r].isalnum:
                r -= 1
            if s[l] != s[r]:
                return False
            l += 1
            r -= 1
        return True