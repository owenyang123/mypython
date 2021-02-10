class Solution(object):
    def validIPAddress(self, IP):
        def isIPv4(s):
            if not s:return False
            try:
                if str(int(s)) == s and 0 <= int(s) <= 255:return True
                return False
            except:
                return False
        def isIPv6(s):
            if not s:return False
            try:
                if len(s) <= 4 and int(s, 16) >= 0:return True
                return False
            except:
                return False
        if IP.count(".") == 3 and all(isIPv4(i) for i in IP.split(".")):
            return "IPv4"
        if IP.count(":") == 7 and all(isIPv6(i) for i in IP.split(":")):
            return "IPv6"
        return ""
#switch speed
def generate_dict(filename):
    switch_data={}
    with open(filename, 'r') as file:
        for row in file.readlines():
            try:
                temp = [i for i in row.replace("\n", "").split(",") if i != ""]
                if temp and (temp[1].startswith("xe") or temp[1].startswith("ge")):
                    if temp[0] in switch_data:switch_data[temp[0]].append([temp[1],int(temp[2]),int(temp[3])])
                    else:switch_data[temp[0]]=[[temp[1],int(temp[2]),int(temp[3])]]
            except:pass
    return switch_data
#findnext
def findhightalk(dict1):
    if not dict1:return []
    res=[]
    for i in dict1:
        temp = [i, 0]
        for j in zip(*dict1[i])[1:]:
            temp[1] += sum(j)
        res.append(temp)
    return sorted(res,key=lambda x:x[1])[-1]
print findhightalk(generate_dict('switch.csv'))
#remove workds in file
infile = r"messy_data_file.txt"
outfile = r"cleaned_file.txt"

delete_list = ["firstname1 lastname1","firstname2 lastname2"....,"firstnamen lastnamen"]
fin=open(infile,"")
fout = open(outfile,"w+")
for line in fin:
    for word in delete_list:
        line = line.replace(word, "")
    fout.write(line)
fin.close()
fout.close()
# read the log2 first,only get bipedal's data,the data format is a list [STRIDE_LENGTH,LEG_LENGTH],name as the key of dict
#formular ((STRIDE_LENGTH / LEG_LENGTH) - 1) * SQRT(LEG_LENGTH * g)


def generatedata(file1,file2，pattern):
    dino_dict = {}
    with open(file2, 'r') as file:
        for row in file.readlines():
            temp=[i for i in row.replace("\n","").split(",") if i!=""]
            if temp and temp[-1]==pattern:dino_dict[temp[0]]=[float(temp[1])]
    with open(file1, 'r') as file:
        for row in file.readlines():
            temp=[i for i in row.replace("\n","").split(",") if i!=""]
            if temp and temp[0] in dino_dict: dino_dict[temp[0]].append(float(temp[1]))
    return dino_dict
#fuction to check the speed
def caulatespeed(dict1):
    if not dict1:return []
    res=[]
    for i in dict1.keys():
#to avoid some corner case only one parameter in dict
        if len(dict1[i])>1:
            speed=((dict1[i][0]/dict1[i][1])-1)*((dict1[i][1]*9.8)**0.5)
            res.append([i,speed])
    res.sort(key=lambda x:x[1],reverse=True)
    return [i[0] for i in res]
print caulatespeed(dino_dict)

class Solution(object):
    def addTwoNumbers(self, l1, l2):
        temp1,temp2=[],[]
        while l1:
            temp1.append(str(l1.val))
            l1=l1.next
        while l2:
            temp2.append(str(l2.val))
            l2=l2.next
        res=[ListNode(int(i)) for i in self.addtwostring("".join(temp1),"".join(temp2))]
        for i in range(len(res)-1):
            res[i].next=res[i+1]
        res[-1].next=None
        return res[0]
    def addtwostring(self,str1,str2):
        if not str1 and str2:return str2
        if not str2 and str1:return str1
        if len(str2)>len(str1):return self.addtwostring(str2,str1)
        l1=list(str1)
        l2=["0"]*(len(str1)-len(str2))+list(str2)
        carry=0
        sumstr=""
        for i in range(len(l1)-1,-1,-1):
            temp=int(l1[i])+int(l2[i])+carry
            sumstr+=str(temp%10)
            if temp>=10:carry=1
            else:carry=0
        if carry==1:return "1"+sumstr[::-1]
        else:return sumstr[::-1]

print(addtwostring("9999999","2"))




#sort
def bubble(arr):
    def swap(i,j):
        arr[i],arr[j]=arr[j],arr[i]
    n=len(arr)
    swapped=True
    x=-1
    while swapped :
        swapped=False
        x=x+1
        for i in range(1,n-x):
            if arr[i-1]>arr[i]:
                swap(i-1,i)
                swapped=True
    return arr
#next
import commands
import threading

#host->ip
hostlist=[]
with open('log.csv', 'r') as file:
    for row in file.readlines():
        temp=row.replace("\n","").split(",")
        if temp[0].isalnum():hostlist.append(temp[1])
res = {}
def findipadd(str1):
    global res
    cmd = "nslookup " + str1
    _, result = commands.getstatusoutput(cmd)
    temp = result.replace("\t", '').split("\n")
    if len(temp)>5:res[str1]=temp[-2].split(" ")[-1]
    else:res[str1]='0.0.0.0'
    return

if __name__ == '__main__':
    instance = []
    for i in hostlist:
        trd = threading.Thread(target=findipadd, args=(i,))
        trd.start()
        instance.append(trd)
    for thread in instance:
        thread.join()
    print res
#next
class Solution(object):
    def smallerNumbersThanCurrent(self, nums):
        dict1={}
        for i in  nums:
            dict1[i]=dict1.get(i,0)+1
        temp=sorted(dict1.items(),key=lambda x:x[0])
        sum1,dict2=0,{}
        for i in temp:
            dict2[i[0]]=sum1
            sum1+=i[1]
        return [dict2[i] for i in nums]
'''
from pprint import pprint

from netmiko import ConnectHandler

def send_show_command(device, commands):
    result = {}
    try:
        with ConnectHandler(**device) as ssh:
            ssh.enable()
            for command in commands:
                output = ssh.send_command(command)
                result[command] = output
        return result
    except :
        print("error")

if __name__ == "__main__":
    device = {
        "device_type": "juniper",
        "ip": "10.85.174.59",
        "username": "labroot",
        "password": "lab123",
        "port":22
    }
    result = send_show_command(device, ["show arp","show route"])
    with open("Output.txt", "w") as out:
        for i in result:
            out.write(device["ip"]+"  "+i+"\n")
            out.write(result[i])

    
with open('2020-07-13.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        print row
with open('2020-07-13.csv', 'r') as file:
    for row in file.readlines():
        if row:print row.replace("\n","").replace("\r","").split(',')
'''


def subarraySum(self, nums, k):
    sums = {0: 1}  # prefix sum array
    res = s = 0
    for n in nums:
        s += n  # increment current sum
        res += sums.get(s - k, 0)  # check if there is a prefix subarray we can take out to reach k
        sums[s] = sums.get(s, 0) + 1  # add current sum to sum count
    return res


class Solution(object):
    def toGoatLatin(self, S):
        local_set=set(["a","e","i","o","u","A","E","I","O","U"])
        list1=S.split(" ")
        for i,temp in enumerate(list1):
            if temp[0] in local_set:list1[i]=temp+"ma"+"a"*(i+1)
            else:list1[i]=temp[1:]+temp[0]+"ma"+"a"*(i+1)
        return " ".join(list1)

class Solution(object):
    def numDecodings(self, s):
        if not s or s[0]=="0":
            return 0
        dp = [0 for x in range(len(s) + 1)]
        dp[0] = 1
        dp[1] = 1
        for i in range(2, len(s) + 1):
            if 0 < int(s[i-1]) <= 9:
                dp[i] += dp[i - 1]
            if 10<=int(s[i-2:i]) <= 26:
                dp[i] += dp[i - 2]
        return dp[-1]

class Solution(object):
    def numDecodings(self, s):
        return self._rec_helper(s)
    def _rec_helper(self, data):
        # Base Case 1: Empty string
        if not data:return 1
        first_call, second_call = 0, 0
        if 1 <= int(data[:1]) <= 9:
            first_call = self._rec_helper(data[1:])
        if 10 <= int(data[:2]) <= 26:
            second_call = self._rec_helper(data[2:])

        return first_call + second_call

class Solution(object):
    def reverseVowels(self, s):
        if len(s)<=1:return s
        set1=set(list("aeiou"))
        list1=[i for i in s if i.lower() in set1]
        str1=""
        for i in s:
            if i.lower() not in set1:str1+=i
            else:str1+=list1.pop()
        return str1


class Solution(object):
    def subsets(self, nums):
        if not nums: return [[]]
        len1 = len(nums)
        if len1 == 1: return [[], nums]
        self.l = [[]]
        self.helper(nums, [])
        return self.l
    def helper(self, nums, temp):
        if len(nums) == 1:
            self.l.append(temp + [nums[0]])
            return
        for i in range(len(nums)):
            self.l.append(temp + [nums[i]])
            self.helper(nums[i + 1:], temp + [nums[i]])

class Solution(object):
    def subsetsWithDup(self, nums):
        if not nums: return [[]]
        len1 = len(nums)
        if len1 == 1: return [[], nums]
        nums.sort()
        self.l = [[]]
        self.helper(nums, [])
        return self.l
    def helper(self, nums, temp):
        if len(nums) == 1:
            if temp + [nums[0]] not in self.l:self.l.append(temp + [nums[0]])
            return
        for i in range(len(nums)):
            if temp + [nums[i]] not in self.l:self.l.append(temp + [nums[i]])
            self.helper(nums[i + 1:], temp + [nums[i]])

class Solution(object):
    def validPalindrome(self, s):
        left, right = 0, len(s) - 1
        while left < right:
            if s[left] != s[right]:
                one, two = s[left:right], s[left + 1:right + 1]
                return one == one[::-1] or two == two[::-1]
            left, right = left + 1, right - 1
        return True


class Solution(object):
    def calculate(self, s):
        if not s:return "0"
        stack, num, sign = [], 0, "+"
        for i in range(len(s)):
            if s[i].isdigit():
                num = num*10+int(s[i])
            if (not s[i].isdigit() and not s[i].isspace()) or i == len(s)-1:
                if sign == "-":stack.append(-num)
                elif sign == "+":stack.append(num)
                elif sign == "*":stack.append(stack.pop()*num)
                else:
                    tmp = stack.pop()
                    if tmp//num < 0 and tmp%num != 0:stack.append(tmp//num+1)
                    else:stack.append(tmp//num)
                sign = s[i]
                num = 0
        return sum(stack)


class Solution:
    """
    @param A: An array of Integer
    @return: an integer
    """
    def longestIncreasingContinuousSubsequence(self, A):
        if not A:return 0
        if len(A)==1:return 1
        count,temp=0,1
        for i in range(1,len(A)):
            if A[i]-A[i-1]>0:
                temp+=1
            else:
                count=max(count,temp)
                temp=1
        count=max(count,temp)
        temp=1
        for i in range(len(A)-1,0,-1):
            if A[i]-A[i-1]<0:
                temp+=1
            else:
                count=max(count,temp)
                temp=1
        count=max(count,temp)
        return count
#
with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(10)
#
class Solution:
    def restoreIpAddresses(self, ipstr):
        if not ipstr or len(ipstr) <= 1:return []
        list1 = []
        if len(ipstr) < 4 or len(ipstr) > 12 or not ipstr:return []
        list1 = []
        for i in range(0, 3):
            if self.helper(ipstr[0:i + 1]) :
                temp1 = ipstr[0:i + 1] + "."
                layer1 = ipstr[i + 1:]
                for j in range(0, 3):
                    if j < len(layer1) - 1 and self.helper(layer1[0:j + 1]):
                        temp2 = layer1[0:j + 1] + "."
                        layer2 = layer1[j + 1:]
                        for z in range(0, 3):
                            if z < len(layer2) - 1 and self.helper(layer2[0:z + 1]) and self.helper(layer2[z + 1:]):
                                temp3 = layer2[0:z + 1] + "." + layer2[z + 1:]
                                list1.append(temp1 + temp2 + temp3)
        return list1
    def helper(self,s):
        if not s:return False
        if str(int(s)) == s and 0 <= int(s) <= 255:return True
        return False


class Solution(object):
    def findMaxAverage(self, nums, k):
        sum1 = sum(nums[0:k])
        max1 = float(sum1) / k
        if k == len(nums): return max1
        for i in range(k, len(nums)):
            sum1 = sum1 - nums[i - k] + nums[i]
            max1 = max(max1, float(sum1) / k)
        return max1


class Solution(object):
    def intersection(self, nums1, nums2):
            if not nums1 or not nums2:return []
            if len(nums2)>len(nums1):return self.intersection(nums2, nums1)
            set1=set(nums2)
            res=set([])
            for i in nums1:
                if i in set1:res.add(i)
            return list(res)

class Solution(object):
    def intersection2(self, nums1, nums2):
        set1=set(nums1)
        set2=set(nums2)
        if len(set1)>len(set2):return self.intersection(nums2, nums1)
        l=[]
        for i in set1:
            if i in set2:
                l.append(i)
        return l
def intersection1(self, nums1, nums2):
    if not nums1 or not nums2:return []
    res=[]
    i,j,l1,l2,res=0,0,len(nums1),len(nums2),[]
    while(i<l1 and j<l2):
        if nums1[i]==nums2[j]:
            res.append(nums1[i])
            i+=1
            j+=1
        elif nums[i]>nums[j]:j+=1
        else:i+=1
    return res

import collections
class Solution:
    def intersection(self, nums1, nums2):
        if not nums1 or not nums2:return []
        x1=collections.Counter(nums1)
        x2=collections.Counter(nums2)
        l=[]
        for i in x1:
            if i in x2:
                temp=min(x1[i],x2[i])
                l+=[i]*temp
        return l
#next

class Solution:
    def expressionExpand(self, s):
        if not s:return ""
        if "[" not in s:return s
        temp=self.helper(s)
        return self.expressionExpand(s[0:temp[0]-temp[3]]+(s[temp[0]+1:temp[1]])*temp[2]+s[temp[1]+1:])
    def helper(self,s):
        b,e=0,0
        for i in range(len(s)):
            if s[i]=="[":b=i
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
#next
def maxSubArray(self, nums):
    min_sum, max_sum = 0, -sys.maxsize
    prefix_sum = 0
    for num in nums:
        prefix_sum += num
        max_sum = max(max_sum, prefix_sum - min_sum)
        min_sum = min(min_sum, prefix_sum)
    return max_sum


class Solution:

    def thirdMax(self, nums):
        if not nums: return None
        nums = list(set(nums))
        nums.sort()
        if len(nums) < 3: return nums[-1]
        return nums[-3]

class Solution:
    def threeSum(self, nums):
        l=[]
        if nums==[]:return []
        nums.sort()
        for i,j in enumerate(nums):
            left=i+1
            right=len(nums)-1
            while (left<right):
                s=j+nums[left]+nums[right]
                if s==0:
                    if [j,nums[left],nums[right]] not in l:
                        l.append([j,nums[left],nums[right]])
                    left=left+1
                    right=right-1
                elif s<0:
                    left=left+1
                elif s>0:
                    right=right-1
        return l

#Next
class Solution:
    """
    @param A: a array
    @return: is it monotonous
    """

    def isMonotonic(self, A):
        if not A: return False
        if len(A) == 1 or len(A) == 2: return True
        x1, x2 = self.helper(A), self.helper(A[::-1])
        return x1 or x2

    def helper(self, A):
        i, j = 0, 1
        while (j < len(A)):
            if A[j] >= A[i]:
                j += 1
                i += 1
            else:
                return False
        return True

class Solution:
    """
    @param n: An integer
    @return: An integer which is the first bad version.
    """
    def findFirstBadVersion(self, n):
        if n==1:return 1
        l,r=0,n
        while(l<r-1):
            m=l+(r-l)/2
            if SVNRepo.isBadVersion(m):r=m
            else:l=m
        return r
#Next
class Solution:
    """
    @param grid: a boolean 2D matrix
    @return: an integer
    """

    def numIslands(self, grid):
        # write your code here
        if not grid or not grid[0]:
            return 0
        ret = 0
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1:
                    ret += 1
                    self.removeIsland(grid, i, j)
        return ret

    def removeIsland(self, grid, i, j):
        grid[i][j] = 0
        if i > 0 and grid[i - 1][j] == 1:
            self.removeIsland(grid, i - 1, j)
        if i < len(grid) - 1 and grid[i + 1][j] == 1:
            self.removeIsland(grid, i + 1, j)
        if j > 0 and grid[i][j - 1] == 1:
            self.removeIsland(grid, i, j - 1)
        if j < len(grid[0]) - 1 and grid[i][j + 1] == 1:
            self.removeIsland(grid, i, j + 1)

#Next
class Solution:
    """
    @param source:
    @param target:
    @return: return the index
    """
    def strStr(self, source, target):
        if not target :return 0
        if target not in source:return -1
        len1=len(target)
        for i in range(len(source)):
            if source[i]==target[0]:
                if source[i:i+len1]==target:return i
#Next two sum

def twoSum(self, numbers, target):
    dict1={}
    for i in range(len(numbers)):
        if target-numbers[i] not in dict1:
            dict1[numbers[i]]=i
        else:return [dict1[target-numbers[i]],i]
    return []
#Next valic bracket

def isValidParentheses(self, s):
    temp1 = []
    dict1 = {")": "(", "]": "[", "}": "{"}
    for i in s:
        if i in "([{":
            temp1.append(i)
        elif i in dict1:
            if not temp1 or dict1[i] != temp1.pop(): return False
    return temp1 == []

class Solution:
    """
    @param a: A number
    @return: Returns the maximum number after insertion
    """
    def InsertFive(self, a):
        if a==0:return 50
        if a>0:
            temp=str(a)
            for i in range(len(temp)):
                if int(temp[i])<=5:return int(temp[0:i]+"5"+temp[i:])
            return int(temp+"5")
        if a<0:
            temp=str(-a)
            for i in range(len(temp)):
                if int(temp[i])>=5:return 0-int(temp[0:i]+"5"+temp[i:])
            return 0-int(temp+"5")


class Solution:
    def lengthOfLIS(self, nums):
        if not nums:
            return 0
        n = len(nums)
        dp = [0] * n
        for i in range(1, n):
            for j in range(i):
                if nums[i] > nums[j]:
                    dp[i] = max(dp[i], 1 + dp[j])

        return 1 + max(dp)
#next

class Solution(object):
    def maximalSquare(self, matrix):
        dp,temp = [[0 for _ in range(len(matrix[0]))] for _ in range(len(matrix))],0
        for i in xrange(0, len(matrix)):
            for j in xrange(0, len(matrix[0])):
                if i == 0 or j == 0:
                    dp[i][j] = int(matrix[i][j])
                elif int(matrix[i][j]) == 1:
                    dp[i][j] = min(dp[i - 1][j - 1], dp[i][j - 1], dp[i - 1][j]) + 1
                temp=max(dp[i][j],temp)
        return temp**2
class Solution(object):
    def validIPAddress(self, IP):
        def isIPv4(s):
            try: return str(int(s)) == s and 0 <= int(s) <= 255
            except: return False

        def isIPv6(s):
            try: return len(s) <= 4 and int(s, 16) >= 0
            except: return False

        if IP.count(".") == 3 and all(isIPv4(i) for i in IP.split(".")):
            return "IPv4"
        if IP.count(":") == 7 and all(isIPv6(i) for i in IP.split(":")):
            return "IPv6"
        return ""


def nomal_search(wait_list, key):
    left,right = 0,len(wait_list)
    res_index = -1
    while left < right - 1:
        cur = (left+(right-left))//2
        if wait_list[cur] == key:
            res_index = cur
            break
        elif wait_list[cur] < key:left = cur
        else:right = cur
    return res_index


def generate_dict(filename):
    switch_data={}
    with open(filename, 'r') as file:
        for row in file.readlines():
            temp=[ i for i in row.replace("\n","").split(",") if i!=""]
            if temp and (temp[1].startswith("xe") or temp[1].startswith("ge")):
                if temp[0] not in switch_data:switch_data[temp[0]]={temp[1]:{"input":int(temp[2]),"output":int(temp[3])}}
                else:switch_data[temp[0]][temp[1]]={"input":int(temp[2]),"output":int(temp[3])}
    print switch_data
    return switch_data

def findhightalk(dict1):
    if not dict1:return []
    res=[]
    for i in dict1:
        temp = [i, 0]
        for j in dict1[i]:
            temp[1]+=dict1[i][j]["input"]+dict1[i][j]["output"]
        res.append(temp)
    return sorted(res,key=lambda x:x[1])
items = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, items))

number_list = range(-5, 5)
less_than_zero = list(filter(lambda x: x < 0, number_list))
print(less_than_zero)

from functools import reduce
product = reduce((lambda x, y: x * y), [1, 2, 3, 4])


import itertools
class Solution(object):
    def isAdditiveNumber(self, num):
      length = len(num)
      for i,j in itertools.combinations(range(1,length),2):
          first, second, remaining = num[:i], num[i:j], num[j:]
          if (first.startswith('0') and first != '0') or (second.startswith('0') and second != '0'):
            continue
          while remaining:
            third = str(int(first) + int(second))
            if not remaining.startswith(third):break
            first = second
            second = third
            remaining = remaining[len(third):]
          if not remaining:
            return True
      return    False

import itertools
l=[]
for i in range(7):
    for  k  in  itertools.combinations([1,2,3,4,5,6,7],i):
        l.append(k)
print l


class Solution(object):
    def titleToNumber(self, s):
        temp=0
        s1=s[::-1]
        for i in range(len(s1)):
            temp+=(ord(s1[i])-64)*(26**i)
        return temp


class Solution(object):
    def convertToTitle(self, num):
        capitals = [chr(x) for x in range(ord('A'), ord('Z') + 1)]
        result = ""
        while num > 0:
            result+=capitals[(num - 1) % 26]
            num = (num - 1) // 26
            print result
        return result[::-1]


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


class Solution:
    """
    @param numbers: Give an array numbers of n integer
    @return: Find all unique triplets in the array which gives the sum of zero.
    """

    def threeSum(self, numbers):
        if len(numbers) < 3:
            return []
        numbers.sort()
        l = []
        for i in range(len(numbers) - 2):
            self.twoSum6(numbers[i + 1:], 0 - numbers[i], l, numbers[i])

        return l

    def twoSum6(self, nums, target, l, num):
        if len(nums) < 2:
            return l
        i = 0
        j = len(nums) - 1
        while (i < j):
            if nums[i] + nums[j] == target:
                if [num, nums[i], nums[j]] not in l:
                    l.append([num, nums[i], nums[j]])
                i += 1
                j -= 1
            elif nums[i] + nums[j] > target:
                j -= 1
            else:
                i += 1
        return


class Solution:
    # @param A : list of integers
    # @param B : integer
    # @return an integer
    def threeSumClosest(self, nums, target):
        # write your code here
        if len(nums) < 3 or target is None:
            return 0

        nums.sort()

        n = len(nums)
        min_diff = sys.maxsize
        res = None

        for i in range(n):
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            l, r = i + 1, n - 1

            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s == target:
                    return s

                if s < target:
                    l += 1
                else:
                    r -= 1

                if abs(target - s) < min_diff:
                    min_diff = abs(target - s)
                    res = s

        return res

def main():
    try:
        return 0
    except:
        return 1

if __name__ == "__main__":
    sys.exit(main())

import itertools
class Solution(object):
    def canThreePartsEqualSum(self, arr):
        if not arr or len(arr)<3:return False
        if sum(arr)%3==0:sum1=sum(arr)/3
        else:return False
        temp=self.helper(arr,sum1)
        if temp[0]:
            return self.helper(arr[temp[1]+1:],sum1)[0]
        return False
    def helper(self,arr,target):
        if not arr:return (False,-1)
        if len(arr)<2:return (False,-1)
        sum1=arr[0]
        if sum1==target:return (True,0)
        for i in range(1,len(arr)):
            sum1+=arr[i]
            if sum1==target and i!=len(arr)-1:return (True,i)
        return (False,-1)
import itertools
class Solution(object):
    def canThreePartsEqualSum(self, arr):
        if not arr or len(arr)<3:return False
        for i ,j in itertools.combinations(range(1,len(arr)),2):
            temp1,temp2,temp3=arr[0:i],arr[i:j],arr[j:]
            if sum(temp1)==sum(temp2)==sum(temp3):return True
        return False

def canThreePartsEqualSum(self, arr):
    total = sum(arr)
    if total % 3 != 0: return False
    count, cumsum, target = 0, 0, total // 3
    for num in arr:
        cumsum += num
        if cumsum == target:
            cumsum = 0
            count += 1
    return count >= 3
class Solution(object):
    def robotSim(self, commands, obstacles):
        direct={0:"North",2:"South",-2:"South",1:"West",-3:"West",-1:"East",3:"East"}
        cur,x,y,res=0,0,0,0
        set1=set(map(tuple, obstacles))
        for i in commands:
            if i==-1:
                cur-=1
                if abs(cur)>=4:cur=abs(cur)-4
            if i==-2:
                cur+=1
                if abs(cur)>=4:cur=abs(cur)-4
            if i>0:
                for _ in range(i):
                    if direct[cur]=="North":
                        tempx,tempy=x,y+1
                        if (tempx,tempy) in set1:break
                        x,y=tempx,tempy
                    elif direct[cur]=="South":
                        tempx,tempy=x,y-1
                        if (tempx,tempy) in set1:break
                        x,y=tempx,tempy
                    elif direct[cur]=="East":
                        tempx,tempy=x+1,y
                        if (tempx,tempy) in set1:break
                        x,y=tempx,tempy
                    else:
                        tempx,tempy=x-1,y
                        if (tempx,tempy) in set1:break
                        x,y=tempx,tempy
                res=max(res, x**2+y**2)
        return res
class Solution(object):
    def findKthLargest(self, nums, k):
        ans = heapq.nlargest(k, nums)
        return ans[-1]

class Solution(object):
    def findKthLargest(self, nums, k):
        if not nums: return None
        nums.sort(key=lambda x: 0 - x)
        if k > len(nums): return nums[-1]
        return nums[k - 1]


class Solution(object):
    def gcdOfStrings(self, str1, str2):
        if not str2 or not str1: return ""
        if len(str2) > len(str1): return self.gcdOfStrings(str2, str1)
        if str1.startswith(str2):
            if not str1[len(str2):]: return str1
            return self.gcdOfStrings(str1[len(str2):], str2)
        else:
            return ""

class Solution(object):
    def findOcurrences(self, text, first, second):
        list1 = text.split()
        res=[]
        for i in range(2,len(list1)):
            if list1[i-2]==first and list1[i-1]==second:res.append(list1[i])
        return res
class Solution(object):
    def distributeCandies(self, candies, num_people):
        l=[0]*num_people
        count=0
        while candies>0:
            if candies>=count+1:
                l[count%num_people]+=count+1
                candies-=count+1
            else:
                l[count%num_people]+=candies
                candies=0
            count+=1
        return l

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
    def arraysIntersection(self, arr1, arr2, arr3):
        set1, set2, set3 = set(arr1), set(arr2), set(arr3)
        temp = set([])
        for i in set1:
            if i in set2 and i in set3: temp.add(i)

        return sorted(list(temp))


class Solution(object):
    def arraysIntersection(self, arr1, arr2, arr3):
        i = j = k = 0
        res = []
        while i < len(arr1) and j < len(arr2) and k < len(arr3):
            if arr1[i] == arr2[j] == arr3[k]:
                res.append(arr1[i])
                i += 1
                j += 1
                k += 1
                continue
            max_ = max(arr1[i], arr2[j], arr3[k])
            if arr1[i] < max_:
                i += 1
            if arr2[j] < max_:
                j += 1
            if arr3[k] < max_:
                k += 1
        return res

class Solution(object):
    def productExceptSelf(self, nums):
        if not nums:return None
        if len(nums)==1:return [1]
        temp=[i for i in nums if i!=0]
        if not temp or len(temp)<=len(nums)-2:return [0]*len(nums)
        l,pro1,pro2=[],reduce((lambda x,y:x*y),nums),reduce((lambda x,y:x*y),temp)
        for i in nums:
            if i!=0:l.append(pro1/i)
            else:l.append(pro2)
        return l
class Solution(object):
    def addBinary(self, a, b):
        if not a:a="0"
        if not b:b="0"
        return str(bin(int(a,2)+int(b,2)))[2:]
class Solution:
    def isAlienSorted(self, words,order):
        dict1={x:i for i,x in enumerate(order)}



class Solution:
    def isAlienSorted(self, words,order) :
        dict1={x:i for i,x in enumerate(order)}
        return sorted(words, key=lambda x: [dict1[c] for c in x]) == words

class Solution(object):
    def merge(self, nums1, m, nums2, n):
        for i in range(m,m+n):
            nums1[i]=nums2[i-m]
        nums1.sort()
        return nums1

class Solution(object):
    def countAndSay(self, n):
        if n==1:return "1"
        if n==2:return "11"
        temp2,temp3='11',""
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
class Solution(object):
    def reverse(self, x):
        if x<0:
            return 0-self.reverse(-x)
        str1=str(x)
        k=int(str1[::-1])
        if k>=2**31:
            return 0
        return int(str1[::-1])
class Solution(object):
    def isPalindrome(self, s):
        l=[i.lower() for i in s if i.isalnum() ]
        str1="".join(l)
        return str1==str1[::-1]
class Solution(object):
    def removeDuplicates(self, S):
        if not S: return s
        stack = []
        for ch in S:
            if stack and stack[-1]==ch:
                stack.pop()
                continue
            stack.append(ch)
        return "".join(stack)

class Solution(object):
    def removeDuplicates(self, S):
        if not S:return ""
        for i in range(1,len(S)):
            if S[i]==S[i-1]:
                return self.removeDuplicates(S[0:i-1]+S[i+1:])
        return S


import collections

class Solution(object):
    def canPermutePalindrome(self, s):
        temp = collections.Counter(s)
        return sum([1 for i in temp if temp[i] % 2 == 1]) < 2

class Solution(object):
    def isToeplitzMatrix(self, matrix):
        for i in range(len(matrix)):
            for j in range(len(matrix[0])):
                if i-1<0 or j-1<0:continue
                if matrix[i][j]!=matrix[i-1][j-1]:return False
        return True
class Solution(object):
    def islandPerimeter(self, grid):
        numsq = 0
        for i in grid:
            numsq += i.count(1)
        count_adj = 0
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1: count_adj += self.helper(grid, i, j)
        return numsq * 4 - count_adj

    def helper(self, grid, i, j):
        count = 0
        if i - 1 >= 0 and grid[i - 1][j] == 1: count += 1
        if i + 1 <= len(grid) - 1 and grid[i + 1][j] == 1: count += 1
        if j - 1 >= 0 and grid[i][j - 1] == 1: count += 1
        if j + 1 <= len(grid[0]) - 1 and grid[i][j + 1] == 1: count += 1
        return count
class Solution(object):
    def singleNumber(self, nums):
        return sum(list(set(nums)))*2-sum(nums)
class Solution(object):
    def moveZeroes(self, nums):
        temp=[i for i in nums if i!=0]
        nums.sort(key=lambda x:abs(x),reverse=True)
        for i in range(len(temp)):
            nums[i]=temp[i]
        return nums
class Solution(object):
    def moveZeroes(self, nums):
        i = 0
        for j in range(len(nums)):
            if nums[j] != 0:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
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
    def isMonotonic(self, A):
        flag1=all([A[i]<=A[i+1] for i in range(len(A)-1)])
        flag2=all([A[i]>=A[i+1] for i in range(len(A)-1)])
        return flag1 or flag2


class Solution(object):
    def findSpecialInteger(self, arr):
        x = int(len(arr) * 0.25)
        for i in range(len(arr) - x):
            if arr[i] == arr[i + x]: return arr[i]
        return None

class Solution:
    def minRemoveToMakeValid(self, s):
        index,stack=[],[]
        for i in range(len(s)):
            if s[i]=="(":stack.append(i)
            elif s[i]==")":
                if len(stack)==0:index.append(i)
                else:stack.pop()
        ans=""
        arr=[1]*(len(s))
        for i in index:arr[i]=0
        for i in stack:arr[i]=0
        for i in range(len(s)):if arr[i]==1:ans+=s[i]
        return ans


class Solution(object):
    def kClosest(self, points, K):
        points.sort(key=lambda x: x[0] * x[0] + x[1] * x[1])
        return points[:K]


class Solution(object):
    def isSymmetric(self, root):
        if not root: return True
        if not root.right and not root.left: return True
        if not root.right or not root.left: return False
        self.l1 = []
        self.l2 = []
        self.ldfs(root)
        self.rdfs(root)
        return self.l1 == self.l2

    def ldfs(self, root):
        self.l1.append(root.val)
        if not root.right and not root.left: return
        if root.left:
            self.ldfs(root.left)
        else:
            self.l1.append(-1)
        if root.right:
            self.ldfs(root.right)
        else:
            self.l1.append(-1)

    def rdfs(self, root):
        self.l2.append(root.val)
        if not root.right and not root.left: return
        if root.right:
            self.rdfs(root.right)
        else:
            self.l2.append(-1)
        if root.left:
            self.rdfs(root.left)
        else:
            self.l2.append(-1)

class Solution(object):
    def isStrobogrammatic(self, num):
        dict1={1:1,2:None,3:None,4:None,5:None,6:9,7:None,8:8,9:6,0:0}
        temp1=""
        for i in num[::-1]:
            if dict1[int(i)]==None:return False
            temp1+=str(dict1[int(i)])
        return temp1==num
class Solution(object):
    def addToArrayForm(self, A, K):
        temp="".join([str(i) for i in A])
        res=[int(i) for  i in str(int(temp)+K)]
        return res
class Solution(object):
    def pivotIndex(self, nums):
        sum1=sum(nums)
        sum2=0
        for i in range(len(nums)):
            if sum2==(sum1-nums[i])/2 and (sum1-nums[i])%2==0:return i
            sum2+=nums[i]
        return -1
class Solution(object):
    def findKthPositive(self, arr, k):
        i = 1
        set1=set(arr)
        while k > 0:
            if i not in set1:
                k -= 1
            i += 1
        return i-1
class Solution(object):
    def canAttendMeetings(self, intervals):
        if not intervals or len(intervals)==1:return True
        intervals.sort(key=lambda x:x[0])
        for i in range(1,len(intervals)):
            if intervals[i][0]<intervals[i-1][1]:return False
        return True

        res=[int(i) for  i in str(int(temp)+K)]

class Solution(object):
    def findMissingRanges(self, nums, lower, upper):
        if not nums:
            if lower==upper:return [str(lower)]
            return [str(lower)+"->"+str(upper)]
        if nums[0]>lower:nums.insert(0,lower-1)
        if nums[-1]<upper:nums.append(upper+1)
        nums.sort()
        res=[]
        for i in range(1,len(nums)):
            if nums[i]-nums[i-1]==1:continue
            if nums[i]-nums[i-1]==2:res.append(str(nums[i-1]+1))
            else:res.append(str(nums[i-1]+1)+"->"+str(nums[i]-1))
        return res
class Solution(object):
    def subarraySum(self, nums, k):
            sums = {0: 1}  # prefix sum array
            res = s = 0
            for n in nums:
                s += n  # increment current sum
                res += sums.get(s - k, 0)  # check if there is a prefix subarray we can take out to reach k
                sums[s] = sums.get(s, 0) + 1  # add current sum to sum count
            return res
class Solution(object):
    def subarraySum(self, nums, k):
            sums = {0: 1}  # prefix sum array
            res = s = 0
            for n in nums:
                s += n  # increment current sum
                res += sums.get(s - k, 0)  # check if there is a prefix subarray we can take out to reach k
                sums[s] = sums.get(s, 0) + 1  # add current sum to sum count
            return res
class Solution(object):
    def intervalIntersection(self, f, s):
        if not f or not s:return []
        res,i,j=[],0,0
        while (i<len(f) and j<len(s)):
            small,big=max(f[i][0],s[j][0]),min(f[i][1],s[j][1])
            if small<=big:res.append([small,big])
            if f[i][1]<s[j][1]:i+=1
            else:j+=1
        return res

class Solution(object):
    def longestOnes(self, a, k):
        st, res = 0, 0
        for i in range(len(a)):
            if a[i] == 0 and k:
                k -= 1
            elif a[i] == 0:
                while a[st] != 0:
                    st += 1
                st += 1
            res = max(res, i-st+1)
        return res