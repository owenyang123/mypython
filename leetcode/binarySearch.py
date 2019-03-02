class Solution:
    def binarySearch(self, nums, target):
        if nums==[] or target==None or target>nums[-1] or target<nums[0]:
            print 123
            return -1
        if target==nums[0]:
            return 0
        if target==nums[-1]:
            return len(nums)-1
        i=0
        j=len(nums)-1
        mid= (i+j)/2
        while (i<j-1):
            if nums[mid]==target :
                while (nums[mid]==target):
                    mid=mid-1
                return mid+1
            if nums[mid]<target:
                i=mid
                mid=(i+j)/2
            elif nums[mid]>target:
                j=mid
                mid = (i + j) / 2
            print mid,i,j
        return -1

k=Solution()
print k.binarySearch([4,5,9,9,10,12,13,14,15,15,18],9)

