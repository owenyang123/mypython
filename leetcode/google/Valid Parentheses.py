class Solution:

    def isValidParentheses(self, s):
        if not s:
            return False
        stack = []
        mapping = {'(': ')', '{': '}', '[': ']'}
        for i in s:
            if i in mapping:
                stack.append(i)
            elif not stack or (mapping[stack.pop()] != i):
                return False

        return len(stack) == 0

