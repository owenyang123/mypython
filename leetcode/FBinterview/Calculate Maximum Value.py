class Solution:
    """
    @param str: the given string
    @return: the maximum value
    """
    def calcMaxValue(self, str):
        # write your code here
        if (len(str) == 0) :
            return 0
        res = int(str[0]);
        for i in range(1, len(str)) :
            val = int(str[i]);
            if(val == 0 or val == 1 or res <= 1):
                res += val
            else :
                res *= val
        return res