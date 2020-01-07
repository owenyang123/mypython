class Solution:
    # @param A : list of integers
    # @param B : integer
    # @param C : integer
    # @return an integer
    def solve(self, A):
        if not A:
            return 0
        B=len(A)
        combinations = []
        self.dfs(A, 0, [], combinations, B)
        n = 0
        return combinations

    def dfs(self, nums, index, combination, combinations, B):
        combinations.append(list(combination))

        for i in range(index, len(nums)):
            combination.append(nums[i])
            self.dfs(nums, i +1, combination, combinations, B)
            combination.pop()

testlist=[8,89,2,3,4,5,6,7]

k=Solution()
x=k.solve(testlist)
print x

l=["1","2","3"]
print "".join(l)


