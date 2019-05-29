class Solution:
    """
    @param digits: a number represented as an array of digits
    @return: the result
    """

    def plusOne(self, digits):
        if not digits:
            return None
        l = [0] * len(digits)
        flag1 = True
        for i in digits:
            if i != 9:
                flag1 = False
                break
        if flag1 == True:
            l.append(1)
            return l[::-1]
        else:
            if digits[-1] != 9:
                digits[-1] += 1
                return digits
            else:
                for i in range(len(digits)):
                    if digits[-1 - i] == 9:
                        digits[-1 - i] = 0
                    else:
                        digits[-1 - i] += 1
                        return digits

