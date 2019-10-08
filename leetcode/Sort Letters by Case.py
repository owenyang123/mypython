class Solution:
    """
    @param: chars: The letter array you should sort by Case
    @return: nothing
    """
    def sortLetters(self, chars):
        if not chars:
            return None
        if len(chars)==1:
            return chars
        left, right = 0, len(chars) - 1

        while left < right:
            while left < right and chars[left].islower():
                left += 1
            while left < right and (not chars[right].islower()):
                right -= 1
            if left < right:
                chars[right], chars[left] = chars[left], chars[right]
                left += 1
                right -= 1

class Solution:
    """
    @param: chars: The letter array you should sort by Case
    @return: nothing
    """
    def sortLetters(self, chars):
        if not chars:
            return None
        if len(chars)==1:
            return chars
        s1,s2="",""
        for i in chars:
            if i.islower():
                s1=s1+i
            else:
                s2=s2+i
        for i in range(len(chars)):
            chars[i]=(s1+s2)[i]
        return s1+s2

