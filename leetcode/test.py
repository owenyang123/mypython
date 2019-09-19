class Solution:
    def luckyNumber(self, n):
        len1 = len(n)
        if len1 % 2 == 1:
            return "3" * (len1 / 2 + 1) + "5" * (len1 / 2 + 1)
        else:
            k = len1 / 2
            if int(n) <= int("3" * k + "5" * k):
                return "3" * k + "5" * k
            elif int(n) > int("5" * k + "3" * k):
                return "3" * (k + 1) + "5" * (k + 1)
            elif n[0] == "4" or (int(n)>):
                return "5" + "3" * k + "5" * (k - 1)
            else:
            if n[0] == "3":
                for i in len(n):
                    if n[i] > 3:


