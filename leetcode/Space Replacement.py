class Solution:
    """
    @param: string: An array of Char
    @param: length: The true length of the string
    @return: The true length of new string
    """
    def replaceBlank(self, string, length):
        if not string:
            return None
        for i in range(len(string)):
            if string[i]==" ":
                string[i]="%20"
