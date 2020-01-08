class Solution:
    """
    @param source : A string
    @param target: A string
    @return: A string denote the minimum window, return "" if there is no such a string
    """

    def minWindow(self, source, target):
        if len(target) > len(source):
            return ""
        temp = 10000000000000
        temp1 = ""
        for i in range(len(source)):
            for j in range(i + 1, len(source) + 1):
                if self.helper(source[i:j], target) and len(source[i:j]) < temp:
                    temp = len(source[i:j])
                    temp1 = source[i:j]
        return temp1

    def helper(self, k, str123):
        for i in str123:
            if str123.count(i)>k.count(i):
                return False
        return True