# clinet
# import socket
# import time
# PORT=6688
# HEADER=64
# FORMAT='utf-8'
#
# DICMSG="done"
# SERVER='10.85.209.89'
# ADDR=(SERVER,PORT)
#
# client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# client.connect(ADDR)
#
# msg = raw_input("What's the symbol of your stock: ")
#
# def send(msg):
#     message=msg.encode(FORMAT)
#     msg_length=len(message)
#     send_length=str(msg_length).encode(FORMAT)
#     send_length+=b' '*(HEADER-len(send_length))
#     client.send(send_length)
#     client.send(message)
#     print client.recv(2048)
#
# send(msg)
# time.sleep(5)
# send(DICMSG)

# sever
# import socket,threading
# import stockplay as sp
#
# PORT=6688
# SERVER=socket.gethostbyname(socket.gethostname())
#
# server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#
# ADDR=('10.85.209.89',PORT)
# print ADDR
# server.bind(ADDR)
#
# HEADER=64
# FORMAT='utf-8'
#
# DICMSG="done"
#
# def handle_clinet(conn,addr):
#     print addr[0]+" is coming with port "+str(addr[1])
#     connected=True
#     while connected:
#         msg_len=conn.recv(HEADER).decode(FORMAT)
#
#         if msg_len:
#             msg_len=int(msg_len)
#             msg=conn.recv(msg_len).decode(FORMAT)
#             print(msg)
#             if msg==DICMSG:connected=False
#             else:
#                 temp1=sp.caifuziyou([msg])[0]
#                 temp= " ".join([str(i) for i in temp1])
#                 print "sent "+temp
#                 conn.send(temp.encode(FORMAT))
#     conn.close()
#
#
# def start():
#     server.listen(5)
#     while True:
#         conn,addr=server.accept()
#         thread=threading.Thread(target=handle_clinet,args=(conn,addr))
#         thread.start()
#
# print "ready"
#
# start()

'''
#read big file

from functools import partial

def read_from_file(filename, block_size = 1024 * 8):
    with open(filename, "r") as fp:
        for chunk in iter(partial(fp.read, block_size), ""):
            yield chunk

def read_from_file(filename, block_size = 1024 * 8):
    with open(filename, "r") as fp:
        while chunk := fp.read(block_size):
            yield chunk

import collections
import re,copy


l=[1,2,3,4,6]

with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(10)


re_telephone = re.compile(r'^(\d{3})-(\d{3,8})$')
print re_telephone.match('010-12345').groups()
print re_telephone.match('010-8086').groups()
('010', '8086')

x={'sea':{'core':["abc"]}}
l1=[["sea","ce","bcd"],["sea1","core","bcd"],["sea","ce","bcd1"],["sea3","ce","bcd1"],["sea","ce","aaabcd1"]]
for i in l1:
    if i[0] in x:
        if i[1] in x[i[0]]:
            x[i[0]][i[1]].append(i[2])
        else:
            x[i[0]][i[1]]=[i[2]]
    else:
        x[i[0]]={i[1]:[i[2]]}
print x
'''
class Solution:

    def sortedArrayToBST(self, num):
        if not num:return None
        temp = len(num) /2
        root = TreeNode(num[temp])
        root.left = self.sortedArrayToBST(num[:temp])
        root.right = self.sortedArrayToBST(num[temp+1:])
        return root

class Solution(object):
    def twoSum(self, nums, target):
        dict1={}
        for i in range(len(nums)):
            if nums[i] in dict1:return [dict1[nums[i]],i]
            dict1[target-nums[i]]=i
        return []

class Solution:
    """
    @param s: an expression includes numbers, letters and brackets
    @return: a string
    """

    def expressionExpand(self, s):
        if not s: return ""
        if "[" not in s: return s
        for i in s:
            if i.isalnum():
                temp = self.helper(s)
                print temp[0],typotemp[1]
                return s[0:i] + self.expressionExpand(s[5:6])*int(i) + s[7:]

    def helper(self, s):
        b, e = 0, 0
        for i in range(len(s)):
            if s[i] == "[":
                b = i
                break
        for i in range(len(s) - 1, -1, -1):
            if s[i] == "]":
                e = i
                break
        return (b, i)

k=Solution()
print k.expressionExpand("abc3[a]")

class Solution:
    """
    @param s: an expression includes numbers, letters and brackets
    @return: a string
    """
    def expressionExpand(self, s):
        if not s:return ""
        if "[" not in s:return s
        temp=self.helper(s)
        return self.expressionExpand(s[0:temp[0]-temp[3]]+(s[temp[0]+1:temp[1]])*temp[2]+s[temp[1]+1:])
    def helper(self,s):
        b,e=0,0
        for i in range(len(s)):
            if s[i]=="[":
                b=i
            if s[i]=="]":
                e=i
                break
        temp,str1=b-1,""
        while(temp>=0):
            if s[temp].isdigit():
                str1+=s[temp]
                temp-=1
            else:break
        return (b,e,int(str1[::-1]),len(str1))


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
    def lengthOfLongestSubstring(self, s):
        if not s:return 0
        if len(set(s))==1:return 1
        max1=len(set(s))
        i,j,temp=0,1,1
        while (i<=len(s)-1):
            if j>i+max1:
                i+=1
            elif len(s[i:j])==len(set(s[i:j])):
                temp=max(temp,len(s[i:j]))
                j+=1
            else:
                i+=1
                j=i+1
        return temp

class Solution(object):
    def lengthOfLongestSubstring(self, s):
        dic, res, start, = {}, 0, 0
        for i, ch in enumerate(s):
            if ch in dic:
                # update the res
                res = max(res, i-start)
                # here should be careful, like "abba"
                start = max(start, dic[ch]+1)
            dic[ch] = i
        # return should consider the last
        # non-repeated substring
        return max(res, len(s)-start)

class Solution(object):
    def lengthOfLongestSubstring(self, s):
        if not s:return 0
        dic, res, start, = {}, 0, 0
        s1=s+s[0]
        for i, ch in enumerate(s1):
            if ch in dic:
                # update the res
                res = max(res, i-start)
                # here should be careful, like "abba"
                start = max(start, dic[ch]+1)
            dic[ch] = i
        # return should consider the last
        # non-repeated substring
        return res


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


from functools import reduce
fruit = ["Apple", "Banana", "Pear", "Apricot", "Orange"]
map_object = map(lambda s: s[0] == "A", fruit)
[True, False, False, True, False]
filter_object = filter(starts_with_A, fruit)
['Apple', 'Apricot']
list = [2, 4, 7, 3]
print(reduce(lambda x, y: x + y, list))
print("With an initial value: " + str(reduce(lambda x, y: x + y, list, 10)))

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
def longestConsecutive(self, nums):
    nums = set(nums)
    best = 0
    for x in nums:
        if x - 1 not in nums:
            y = x + 1
            while y in nums:
                y += 1
            best = max(best, y - x)
    return best
class Solution(object):
    def closedIsland(self, grid):
        n = len(grid)
        m = len(grid[0])
        def dfs(x, y):
            if grid[x][y]==1:return
            grid[x][y] = 1
            if x<n-1:dfs(x + 1, y)
            if x>0:dfs(x - 1, y)
            if y<m-1:dfs(x, y + 1)
            if y>0:dfs(x, y - 1)
        for i in range(m):
            if grid[0][i]==0:dfs(0,i)
            if grid[n-1][i]==0:dfs(n-1,i)
        for i in range(1,n-1):
            if grid[i][0]==0:dfs(i,0)
            if grid[i][-1]==0:dfs(i,m-1)
        count =0
        for i in range(1,n-1):
            for j in range(1,m-1):
                if not grid[i][j]:
                    dfs(i, j)
                    count+=1
        return count
class Solution(object):
    def numSplits(self, s):
        if not s or len(s) == 1: return 0
        if len(s) == 2: return 1
        counter, x2, x1 = 0, {}, {}
        for i in s: x1[i] = x1.get(i, 0) + 1
        for i in s:
            if i in x1:
                x1[i] -= 1
                if x1[i] == 0: del x1[i]
            if i in x2:
                x2[i] += 1
            else:
                x2[i] = 1
            if len(x1) == len(x2): counter += 1
        return counter


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

#emplyee importance
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


#max subarray
class Solution(object):
    def maxSubArray(self, nums):
        if not nums:return None
        if len(nums)==1:return nums[0]
        res,cur,cur1=nums[0],nums[0],nums[0]
        for i in range(1,len(nums)):
            cur+=nums[i]
            res=max(res,cur-cur1,cur)
            cur1=min(cur1,cur)
        return res

class Solution(object):
    def getImportance(self, employees, id):
        A = {}

        def dfs(i):
            return A[i][0] + sum(dfs(j) for j in A[i][1])

        for e in employees:
            A[e.id] = [e.importance, e.subordinates]

        return dfs(id)

class Solution(object):
    def getImportance(self, employees, id):
        if not  employees:return 0
        for i in employees:
            if i.id==id and i.subordinates==[]:return i.importance
            elif i.id==id:
                temp=i.importance
                for j in i.subordinates:
                    temp+=self.getImportance(employees,j)
                return temp
        return 0
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

class Solution(object):
    def moveZeroes(self, nums):
        i,j= 0,0
        def swap(arr,i,j):arr[i],arr[j]= arr[j],arr[i]
        while (j<len(nums)):
            if nums[j]==0:j+=1
            else:
                swap(nums,i,j)
                j+=1
                i+=1
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

class Solution:     #lmv
    def maxProfit(self, prices):
        max_profit, min_price = 0, float('inf')
        for price in prices:
            min_price = min(min_price, price)
            profit = price - min_price
            max_profit = max(max_profit, profit)
        return max_profit

class Solution(object):
    def isPowerOfThree(self, n):
        if n<=0:return False
        if n==1:return True
        if n%3!=0:return False
        return self.isPowerOfThree(n/3)


class Solution(object):
    def isIsomorphic(self, s, t):
        def s2l(str1):
            dict1 = {}
            res, count = [], 0
            for i in str1:
                if i in dict1:
                    res.append(dict1[i])
                else:
                    dict1[i] = count
                    res.append(count)
                    count += 1
            return res
        return s2l(s) == s2l(t)
class Solution(object):
    def isIsomorphic(self, s, t):
        return len(set(zip(s, t))) == len(set(s)) == len(set(t))


class Solution(object):
    def reorderSpaces(self, text):
        if not text: return ""
        temp = [i for i in text.split() if i != ""]
        n = text.count(" ")
        if n == 0: return text
        if len(temp) == 1: return temp[0] + " " * n
        x1 = n // (len(temp) - 1)
        x2 = n % (len(temp) - 1)
        return (" " * x1).join(temp) + " " * x2


class Solution(object):
    def isValid(self, s):
        dict1 = {"(": ")", "[": "]", "{": "}"}
        list1 = []
        for i in s:
            if i.isalnum(): continue
            if i in dict1:
                list1.append(dict1[i])
            elif not list1 or i != list1[-1]:
                return False
            else:
                list1.pop()
        if list1 == []: return True
        return False
class Solution:     #lmv
    def maxProfit(self, prices):
        max_profit, min_price = 0, float('inf')
        for price in prices:
            min_price = min(min_price, price)
            profit = price - min_price
            max_profit = max(max_profit, profit)
        return max_profit

class Solution:
    def rotate(self, A):
        temp=list(zip(*A))
        return [list(i)[::-1] for i in temp]

class Solution(object):
    def mySqrt(self, x):
        if x==1 or x==0:return x
        r = x
        while r*r > x:
            r = (r + x/r) / 2
        return r
class Solution(object):
    def validMountainArray(self, A):
        i, j, n = 0, len(A) - 1, len(A)
        while i + 1 < n and A[i] < A[i + 1]: i += 1
        while j > 0 and A[j - 1] > A[j]: j -= 1
        return 0 < i == j < len(A)- 1


class Solution(object):
    def reverse(self, x):
        if x < 0: return 0 - self.reverse(-x)
        k = int(str(x)[::-1])
        if k >= 2 ** 31: return 0
        return k
import re
pattern=re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
x=pattern.findall("272.168.1.1.23")
print(x)
if re.match(r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", string_IPv6, re.I):
  print "IPv6 vaild"
else:
  print "IPv6 invaild"

class Solution(object):
    def countSquares(self, matrix):
        if not matrix: return 0
        res = 0
        res += sum(matrix[0])
        for i in range(1, len(matrix)): res += matrix[i][0]
        for i in range(1, len(matrix)):
            for j in range(1, len(matrix[0])):
                if matrix[i][j] != 0:
                    matrix[i][j] = matrix[i][j] + min(matrix[i - 1][j], matrix[i][j - 1], matrix[i - 1][j - 1])
                    res += matrix[i][j]
        return res

#area island
class Solution:
    def maxAreaOfIsland(self, grid):
        n = len(grid)
        m = len(grid[0])
        def dfs(x, y):
            if (0 <= x and x < n) and (0 <= y and y < m) and grid[x][y]:
                grid[x][y] = 0
                return dfs(x + 1, y) + dfs(x - 1, y) + dfs(x, y + 1) + dfs(x, y - 1) + 1
            return 0
        max_area = 0
        for i in range(n):
            for j in range(m):
                if grid[i][j]:
                    max_area = max(max_area, dfs(i, j))
        return max_area


class Solution:
    def maxAreaOfIsland(self, grid):
        n = len(grid)
        m = len(grid[0])
        matrix = [[0] * (m + 2)]
        for i in grid: matrix.append([0] + i + [0])
        matrix.append([0] * (m + 2))

        def dfs(x, y):
            if matrix[x][y]:
                matrix[x][y] = 0
                return dfs(x + 1, y) + dfs(x - 1, y) + dfs(x, y + 1) + dfs(x, y - 1) + 1
            return 0

        max_area = 0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if matrix[i][j]:
                    max_area = max(max_area, dfs(i, j))

        return max_area

def maxAreaOfIsland(self, grid):
    grid = {i + j*1j: val for i, row in enumerate(grid) for j, val in enumerate(row)}
    def area(z):
        return grid.pop(z, 0) and 1 + sum(area(z + 1j**k) for k in range(4))
    return max(map(area, set(grid)))

#rotated matrix

class Solution:
    # @param A : list of list of integers
    # @return the same list modified
    def rotate(self, A):
        rows, clos = len(A), len(A[0])
        B = [[0 for x in range(rows)] for y in range(clos)]
        for i in range(clos):
            for j in range(rows):
                B[i][j] = A[rows - 1 - j][i]
        return B
    def rotate(self, A):
        temp=zip(*A)
        return [list(i)[::-1] for i in temp]

#internal grid water
class Solution(object):
    def closedIsland(self, grid):
        n = len(grid)
        m = len(grid[0])
        def dfs(x, y):
            if grid[x][y]==1:return
            grid[x][y] = 1
            if x<n-1:dfs(x + 1, y)
            if x>0:dfs(x - 1, y)
            if y<m-1:dfs(x, y + 1)
            if y>0:dfs(x, y - 1)
        for i in range(m):
            if grid[0][i]==0:dfs(0,i)
            if grid[n-1][i]==0:dfs(n-1,i)
        for i in range(1,n-1):
            if grid[i][0]==0:dfs(i,0)
            if grid[i][-1]==0:dfs(i,m-1)
        count =0
        for i in range(1,n-1):
            for j in range(1,m-1):
                if not grid[i][j]:
                    dfs(i, j)
                    count+=1
        return count
class Solution(object):
    def sumOddLengthSubarrays(self, arr):
        l=len(arr)
        if l%2==0:n=l-1
        else:n=l
        sum1=0
        for i in range(l):
            for j in range(1,n+1,2):
                if i+j<=l:
                    sum1+=sum(arr[i:i+j])
        return sum1
    def sumOddLengthSubarrays(self, A):
        res, n = 0, len(A)
        for i, a in enumerate(A):
            res += ((i + 1) * (n - i) + 1) / 2 * a
        return res
class Solution(object):
    def minDifference(self, A):
        A.sort()
        return min(b - a for a, b in zip(A[:4], A[-4:]))

class Solution(object):
    def matrixBlockSum(self, mat, k):
        row, col = len(mat), len(mat[0])
        b = [[mat[0][0] for x in range(col)] for y in range(row)]
        c = [[0 for x in range(col)] for y in range(row)]
        for i in range(1, col):
            b[0][i] = b[0][i - 1] + mat[0][i]
        for i in range(1, row):
            b[i][0] = b[i - 1][0] + mat[i][0]
        for i in range(1, row):
            for j in range(1, col):
                b[i][j] = b[i - 1][j] + b[i][j - 1] - b[i - 1][j - 1] + mat[i][j]
        print
        b
        for i in range(0, row):
            for j in range(0, col):
                x1, x2, y1, y2 = i - k - 1, i + k, j - k - 1, j + k
                if x2 >= row: x2 = row - 1
                if y2 >= col: y2 = col - 1
                c[i][j] = b[x2][y2]
                if x1 < 0 and y1 >= 0: c[i][j] -= b[x2][y1]
                if x1 >= 0 and y1 < 0: c[i][j] -= b[x1][y2]
                if x1 >= 0 and y1 >= 0: c[i][j] = c[i][j] - b[x2][y1] - b[x1][y2] + b[x1][y1]
        return c
# Daily Temperatures
class Solution(object):
    def dailyTemperatures(self, nums):
        res = [0] * len(nums)
        stack = []
        for i in range(len(nums)):
            while stack and nums[i]>nums[stack[-1]]:
                cur=stack.pop()
                res[cur]=i-cur
            stack.append(i)
        return res
list.sort


class Solution(object):
    def countAndSay(self, n):
        s = '1'
        for _ in range(n - 1):
            s = re.sub(r'(.)\1*', lambda m: str(len(m.group(0))) + m.group(1), s)
        return s

    def countAndSay(self, n):
        if n==1:return "1"
        if n==2:return "11"
        temp1,temp2,temp3='1','11',""
        for i in range(3,n+1):
            temp3=self.helper(temp2)
            temp2=temp3
        return temp3
    def helper(self,str1):
        l=[]
        i,j=0,1
        while(j<len(str1)):
            if str1[i]==str1[j]:j+=1
            else:
                l.append([str1[i],j-i])
                i=j
                j+=1
        l.append([str1[i],j-i])
        res=''
        for i in l:
            res+=str(i[1])+i[0]
        return res


class Solution:
    def threeSumClosest(self, num, target):
        num.sort()
        result = num[0] + num[1] + num[2]
        for i in range(len(num) - 2):
            j, k = i + 1, len(num) - 1
            while j < k:
                sum = num[i] + num[j] + num[k]
                if sum == target:
                    return sum

                if abs(sum - target) < abs(result - target):
                    result = sum

                if sum < target:
                    j += 1
                elif sum > target:
                    k -= 1

        return result

class Solution(object):
    def numMatchingSubseq(self, s, words):
        def matchornot(s1,s2):
            i1,i2,l1,l2=0,0,len(s1),len(s2)
            while i1<l1 and i2<l2:
                if s1[i1]==s2[i2]:
                    i1+=1
                    i2+=1
                else:i1+=1
            if i2>=l2:return True
            return False
        res=[]
        for i in words:
            if matchornot(s,i):res.append(i)
        return len(res)

from jnpr.junos import Device
import threading
from lxml import etree
import datetime

list1=["erebus.ultralab.juniper.net","hypnos.ultralab.juniper.net","moros.ultralab.juniper.net","norfolk.ultralab.juniper.net","alcoholix.ultralab.juniper.net","antalya.ultralab.juniper.net","automatix.ultralab.juniper.net","beltway.ultralab.juniper.net","bethesda.ultralab.juniper.net","botanix.ultralab.juniper.net","dogmatix.ultralab.juniper.net","getafix.ultralab.juniper.net","idefix.ultralab.juniper.net","kratos.ultralab.juniper.net","pacifix.ultralab.juniper.net","photogenix.ultralab.juniper.net","rio.ultralab.juniper.net","matrix.ultralab.juniper.net","cacofonix.ultralab.juniper.net","asterix.ultralab.juniper.net","timex.ultralab.juniper.net","greece.ultralab.juniper.net","holland.ultralab.juniper.net","nyx.ultralab.juniper.net","atlantix.ultralab.juniper.net","obelix.ultralab.juniper.net","camaro.ultralab.juniper.net","mustang.ultralab.juniper.net"]
print(len(list1))
dict1={}
def listhw(str1):
    if not str1:return None
    global dict1
    try:
        dev = Device(host = str1, user='labroot', password='lab123')
        dev.open()
        x=dev.rpc.get_chassis_inventory()
        dev.close()
        head=etree.tostring(x).split("\n")
        temp=[str1]
        for i in head:
            if "description" in i:
                temp_str=i.replace("<"," ").replace(">"," ")
                if ("DPC" in temp_str or "MPC" in temp_str or "RE"in temp_str or "CB" in temp_str) and "PMB" not in temp_str:
                    if i[13]=="M" or i[13]=="D" or i[13]=="R":temp.append(i[13:-14])
        dict1[temp[0]]=list(set(temp[1:]))
    except:
        print(str1+" is unreachable")
        pass
    return
instance=[]
for i in list1:
    trd=threading.Thread(target=listhw,args=(i,))
    trd.start()
    instance.append(trd)
for thread in instance:
    thread.join()
temp=[]
for  i in dict1:
    temp.append([i]+sorted(dict1[i]))
temp.sort(key=lambda a:a[0])
for i in temp:
    print (i)

from multiprocessing import Pool
import random
import threading
def testp(str1):
    print("os"+str(random.randrange(100)))
    return str(random.randrange(100))


dict1={}
pool=Pool(16)
for i in range(100):
    dict1.update({i:pool.apply_async(testp,args=("123",))})

for i in dict1:
    print(i,dict1[i].get())
print("#####")
instance=[]
for i in range(1000):
    trd=threading.Thread(target=testp,args=(str(i),))
    trd.start()
    instance.append(trd)
print("#####")
for thread in instance:
    thread.join()