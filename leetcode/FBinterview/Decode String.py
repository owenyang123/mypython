class Solution:
    """
    @param s: an expression includes numbers, letters and brackets
    @return: a string
    """

    def expressionExpand(self, s):
        # write your code here
        stack = []
        num = 0

        for i in range(len(s)):
            if s[i].isdigit():
                num = num * 10 + int(s[i])
            else:
                if s[i] == '[':
                    stack.append(num)
                    num = 0
                else:
                    if s[i] == ']':
                        substr = self.popStack(stack)
                        count = stack.pop()
                        for _ in range(count):
                            stack.append(substr)
                    else:
                        stack.append(s[i])

        return self.popStack(stack)

    def popStack(self, stack):
        helperStack = []
        while stack and type(stack[-1]) is str:
            helperStack.append(stack.pop())

        res = ''
        while helperStack:
            res += helperStack.pop()

        return res


class Solution:
    """
    @param s: an expression includes numbers, letters and brackets
    @return: a string
    """

    def expressionExpand(self, s):
        # write your code here
        if s is None or len(s) == 0:
            return s

        stack = []
        curnum = 0
        for c in s:
            if c == ']':
                cur = ''
                while stack[-1] != '[':
                    cur = stack.pop() + cur
                stack.pop()
                num = stack.pop()
                stack.append(cur * num)
            elif c.isdigit():
                curnum = curnum * 10 + int(c)
            elif c == '[':
                stack.append(curnum)
                stack.append(c)
                curnum = 0
            else:
                stack.append(c)

        return ''.join(stack)

def list2num(self,list1):
         str1 = str(d) for d in list1
         return int(str1)