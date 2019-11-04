import math
class Solution:
    def aplusb(self, a, b):
        while(b!=0):
            carry=a & b
            a=a^b
            b=carry<<1
        return a

k=Solution()
print k.aplusb(5,6)
print math.log(100,10)


class Solution:
    """
    @param nums: an array of Integer
    @param target: target = nums[index1] + nums[index2]
    @return: [index1 + 1, index2 + 1] (index1 < index2)
    """

    def twoSum(self, nums, target):
        dict1 = {}
        for i in range(len(nums)):
            if nums[i] in dict1.keys():
                return [dict1[nums[i]] + 1, i + 1]
            else:
                dict1[target - nums[i]] = i

        return []

class Solution:
    """
    @param nums: an array of Integer
    @param target: target = nums[index1] + nums[index2]
    @return: [index1 + 1, index2 + 1] (index1 < index2)
    """
    def twoSum(self, nums, target):
        i=0
        j=len(nums)-1
        while (i<j):
            if nums[i]+nums[j]==target:
                return [i+1,j+1]
            elif nums[i]+nums[j]>target:
                j-=1
            else:
                i+=1
        return []


class Solution:
    """
    @param nums: an array of integer
    @param target: An integer
    @return: An integer
    """
    def twoSum6(self, nums, target):
        i=0
        j=len(nums)-1
        nums.sort()
        l=[]
        while (i<j-1):
            if nums[i]+nums[j]==target:
                if [nums[i],nums[j]] not in l:
                    l.append([nums[i],nums[j]])
                i+=1
                j-=1
            elif nums[i]+nums[j]>target:
                j-=1
            else:
                i+=1
        print l
        return len(l)


class Solution:
    """
    @param nums: an array of Integer
    @param target: an integer
    @return: [index1 + 1, index2 + 1] (index1 < index2)
    """

    def twoSum7(self, nums, target):
        # write your code here
        if not nums or target is None:
            return [0, 0]
        ndict = {}
        for i in range(len(nums)):
            if (nums[i] + target) not in ndict:
                ndict[nums[i] + target] = i
            elif target == 0:
                return [ndict[nums[i] + target] + 1, i + 1]
        for i in range(len(nums)):
            if nums[i] in ndict:
                k = [ndict[nums[i]] + 1, i + 1]
                k.sort()
                return k

        return [0, 0]


