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


"""
# Definition for Employee.
class Employee(object):
    def __init__(self, id, importance, subordinates):
    	#################
        :type id: int
        :type importance: int
        :type subordinates: List[int]
        #################
        self.id = id
        self.importance = importance
        self.subordinates = subordinates
"""


class Solution(object):
    def getImportance(self, employees, id):
        if not employees: return 0
        for i in employees:
            if i.id == id and i.subordinates == []:
                return i.importance
            elif i.id == id:
                temp = i.importance
                for j in i.subordinates:
                    temp += self.getImportance(employees, j)
                return temp
        return 0


class Solution(object):
    def getImportance(self, employees, id):
        A = {}

        def dfs(i):
            return A[i][0] + sum(dfs(j) for j in A[i][1])

        for e in employees:
            A[e.id] = [e.importance, e.subordinates]

        return dfs(id)
class Solution(object):
    def sortedSquares(self, A):
        return sorted(list(map(lambda x:x*x,A)))

class Solution(object):
    def moveZeroes(self, nums):
        i = 0
        def swap(arr,i,j):arr[i],arr[j]= arr[j],arr[i]
        for j in range(len(nums)):
            if nums[j] != 0:
                swap(nums,i,j)
                i += 1
        return
class Solution:
# @param {string} s
# @return {integer}
    def romanToInt(self, s):
        roman = {'M': 1000,'D': 500 ,'C': 100,'L': 50,'X': 10,'V': 5,'I': 1}
        z = 0
        for i in range(0, len(s) - 1):
            if roman[s[i]] < roman[s[i+1]]:
                z -= roman[s[i]]
            else:
                z += roman[s[i]]
        return z + roman[s[-1]]


class Solution(object):
    def addDigits(self, num):
        if num < 10: return num
        if num < 0: return self.addDigits(0 - num)
        l = [int(i) for i in str(num)]
        return self.addDigits(sum(l))

def generate(self, numRows):
    res = [[1]]
    for i in range(1, numRows):
        res += [map(lambda x, y: x + y, res[-1] + [0], [0] + res[-1])]
    return res[:numRows]

class Solution(object):
    def generate(self, numRows):
        if numRows==1:return [[1]]
        res=[[1]]
        for i in range(1,numRows):
            temp1=[j for j in res[i-1] ]+[0]
            temp2=[0]+[j for j in res[i-1] ]
            res.append([temp1[j]+temp2[j] for j in range(len(temp1))])
        return res

class Solution:
    def floodFill(self, image, sr, sc, newColor):
        old, m, n = image[sr][sc], len(image), len(image[0])
        if old != newColor:
            q = collections.deque([(sr, sc)])
            while q:
                i, j = q.popleft()
                image[i][j] = newColor
                for x, y in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                    if 0 <= x < m and 0 <= y < n and image[x][y] == old:
                        q.append((x, y))
        return image
import collections
class Solution(object):
    def intersect(self, nums1, nums2):
            if not nums1 or not nums2:return []
            c1,c2=collections.Counter(nums1),collections.Counter(nums2)
            res=[]
            for i in c1:
                if i in c2:res+=[i]*min(c1[i],c2[i])
            return res

class Solution:
    def intersect(self, nums1: List[int], nums2: List[int]) -> List[int]:
        nums1.sort()
        nums2.sort()
        pointer1, pointer2, out = 0, 0, list()
        while pointer1 < len(nums1) and pointer2 < len(nums2):
            if nums1[pointer1] == nums2[pointer2]:
                out.append(nums1[pointer1])
                pointer1 += 1
                pointer2 += 1
            elif nums1[pointer1] > nums2[pointer2]:
                pointer2 += 1
            else:
                pointer1 += 1
        return out

class Solution(object):
    def findMaxConsecutiveOnes(self, nums):
        if not nums:return 0
        i,temp,l=0,0,[]
        for i in nums:
            if i==1:
                temp+=1
            else:
                l.append(temp)
                temp=0
        if nums[-1]==1:l.append(temp)
        return max(l)