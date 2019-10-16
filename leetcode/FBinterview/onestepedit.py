class Solution:
    # @param {string} s a string
    # @param {string} t a string
    # @return {boolean} true if they are both one edit distance apart or false
    def isOneEditDistance(self, s, t):
        # Write your code here
        m = len(s)
        n = len(t)
        if abs(m - n) > 1:
            return False

        if m > n:
            return self.isOneEditDistance(t, s)

        for i in xrange(m):
            if s[i] != t[i]:
                if m == n:
                    return s[i + 1:] == t[i + 1:]
                return s[i:] == t[i + 1:]

        return m != n