test1=["((())())","(())()()","(()(()))","((()))()","()(()())","((()()))","()(())()","(()()())","()()()()","()()(())","(()())()","()((()))","(((())))"]
test2=["(((())))","((()()))","((())())","((()))()","(()(()))","(()()())","(()())()","(())(())","(())()()","()((()))","()(()())","()(())()","()()(())","()()()()"]
print  (len(test1),len(test2))
for i in test2:
    if i not in test1:
        print (i)
import copy


class Solution(object):
    def generateParenthesis(self, n):
        if n == 0: return []
        if n == 1: return ["()"]
        if n == 2: return ["()()", "(())"]
        temp = self.generateParenthesis(2)
        temp1 = set()
        for i in range(3, n + 1):
            for j in temp:
                temp1.add("()" + j)
                temp1.add(j + "()")
                temp1.add("(" + j + ")")
            temp = list(temp1)
            temp1 = set()
        return temp
k=Solution()
print (k.generateParenthesis(3))
print (k.generateParenthesis(4))
