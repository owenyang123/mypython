class Solution:
    # @param {string} num a string contains only digits 0-9
    # @param {int} target an integer
    # @return {string[]} return all possibilities
    def addOperators(self, num, target):
        # Write your code here
        self.ans = []
        self.target = target
        for i in xrange(1, len(num) + 1):
            if i > 1 and num[0] == '0':
                continue
            self.helper(num[i:], int(num[:i]), num[:i], int(num[:i]), '#')

        return self.ans

    def helper(self, num, current, tmpAns, pre_val, pre_op):
        if not num:
            if self.target == current:
                self.ans.append(tmpAns)
            return

        for i in xrange(1, len(num) + 1):
            if i > 1 and num[0] == '0':
                continue
            now = int(num[:i])
            self.helper(num[i:], current + now, tmpAns + '+' + num[:i], now, '+')
            self.helper(num[i:], current - now, tmpAns + '-' + num[:i], now, '-')

            if pre_op == '+':
                self.helper(num[i:], current - pre_val + pre_val * now, tmpAns + '*' + num[:i], pre_val * now, pre_op)
            elif pre_op == '-':
                self.helper(num[i:], current + pre_val - pre_val * now, tmpAns + '*' + num[:i], pre_val * now, pre_op)
            else:
                self.helper(num[i:], current * now, tmpAns + '*' + num[:i], pre_val * now, pre_op)