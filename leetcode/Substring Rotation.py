class Solution:
    """
    @param s1: the first string
    @param s2: the socond string
    @return: true if s2 is a rotation of s1 or false
    """
    def isRotation(self, s1, s2):
        if s1=="" and s2=="":
            return False
        if s1=="" or s2=="":
            return False
        if len(s1)!=len(s2):
            return False
        if s1==s2:
            return True
        s=""
        for i in  range(1,len(s2)):
            s=s2[i::]+s2[0:i]
            if s==s1:
                return True
        return False