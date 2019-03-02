class Solution:

    def deduplication(self, nums):
        # write your code here
        st, i = set(), 0
        for num in nums:
            if num not in st:
                st.add(num)
                nums[i] = num
                i += 1

        return i

x=Solution()
print x.deduplication([5,6,7,4,4,4,1,3,1,4,4,2])