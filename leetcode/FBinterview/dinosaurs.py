# read the log2 first,only get bipedal's data,the data format is a list [STRIDE_LENGTH,LEG_LENGTH],name as the key of dict
#formular ((STRIDE_LENGTH / LEG_LENGTH) - 1) * SQRT(LEG_LENGTH * g)

dino_dict={}

with open('log2.csv', 'r') as file:
    for row in file.readlines():
        temp=row.replace("\n","").split(",")
        if temp[-1]=="bipedal":dino_dict[temp[0]]=[float(temp[1])]
with open('log1.csv', 'r') as file:
    for row in file.readlines():
        temp=row.replace("\n","").split(",")
        if temp[0] in dino_dict: dino_dict[temp[0]].append(float(temp[1]))
print dino_dict
#fuction to check the speed
def caulatespeed(dict1):
    if not dict1:return []
    res=[]
    for i in dict1.keys():
        if len(dict1[i])>1:
            speed=((dict1[i][0]/dict1[i][1])-1)*((dict1[i][1]*9.8)**0.5)
            res.append([i,speed])
    res.sort(key=lambda x:x[1],reverse=True)
    return [i[0] for i in res]
print caulatespeed(dino_dict)

def addtwostring(str1,str2):
    if not str1 and str2:return str2
    if not str2 and str1:return str1
    if len(str2)>len(str1):return addtwostring(str2,str1)
    l1=list(str1)
    l2=["0"]*(len(str1)-len(str2))+list(str2)
    carry=0
    sumstr=""
    for i in range(len(l1)-1,-1,-1):
        temp=int(l1[i])+int(l2[i])+carry
        sumstr+=str(temp%10)
        if temp>=10:carry=1
        else:carry=0
    if carry==1:
        return "1"+sumstr[::-1]
    return sumstr[::-1]

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

with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(10)

class Solution:
    def restoreIpAddresses(self, s):
        if not s or len(s) <= 1:
            return []
        ipstr = s
        list1 = []
        if len(ipstr) < 4 or len(ipstr) > 12 or not ipstr:
            return []
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
    def helper(self, str1):
        if len(str1) == 1:
            return True
        if int(str1) > 255:
            return False
        if str1[0] != "0":
            return True
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

def intersection(self, nums1, nums2):
    if not nums1 or not nums2:return []
    if len(nums1)>len(nums2):return self.intersection(nums2, nums1)
    tempset=set(nums2)
    res=set([])
    for i in nums1:
        if i in tempset:res.add(i)
    return list(res)

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
    """
    @param numbers: Give an array numbers of n integer
    @return: Find all unique triplets in the array which gives the sum of zero.
    """
    def threeSum(self, nums):
        l=[]
        if nums==[]:
            return []
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
