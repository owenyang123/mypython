class Solution:

    def sumKEven(self, k):
        sum = 0
        for i in range(1, k + 1):
            num = str(i)
            strnum = num + num[::-1]
            number = int(strnum)
            sum += number
        return sum