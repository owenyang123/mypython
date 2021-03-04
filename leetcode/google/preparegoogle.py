class Solution(object):
    def removeOuterParentheses(self, S):
        res = []
        balance = 0
        i = 0
        for j in range(len(S)):
            if S[j] == "(":balance += 1
            elif S[j] == ")":
                balance -= 1
            if balance == 0:
                res.append(S[i+1:j])
                i = j+1
        return "".join(res)

class Solution(object):
    def rangeSumBST(self, root, L, R):
        if not root:return 0
        self.l=[]
        self.helper(root)
        return sum([i for i in self.l if L<=i<=R])
    def helper(self,root):
        self.l.append(root.val)
        if not root.left and not root.right:return
        if root.left:self.helper(root.left)
        if root.right:self.helper(root.right)

class Solution(object):
    def sortedSquares(self, A):
        return sorted(list(map(lambda x:x*x,A)))

class Solution(object):
    def singleNumber(self, nums):
        return sum(list(set(nums)))*2-sum(nums)
class Solution(object):
    def numUniqueEmails(self, emails):
        email_set = set()
        for email in emails:
            local_name,domain_name = email.split("@")
            local_name =local_name.split('+')[0].replace(".","")
            email = local_name +'@' + domain_name
            email_set.add(email)
        return len(email_set)

class Solution(object):
    def fib(self, A):
        if A==0:return 0
        if A==1 or A==2 :return 1
        if A==3:return 2
        temp1,temp2,temp3=3,2,1
        for i in range(4,A+1):
            temp1=temp2+temp3
            temp3=temp2
            temp2=temp1
        return temp1