class Solution:
    # @param A : list of integers
    # @param B : integer
    # @param C : integer
    # @return an integer
    def solve(self, A, B, C):
        if not A:
            return 0
        combinations = []
        self.dfs(A, 0, [], combinations, B)
        n = 0
        for i in combinations:
            n = n + 1
        return combinations

    def dfs(self, nums, index, combination, combinations, B):
        if len(combination) <= B:
            combinations.append(list(combination))


        for i in range(index, len(nums)):
            combination.append(nums[i])
            self.dfs(nums, i +1, combination, combinations, B)
            combination.pop()

testlist=[ 2, 3, 5, 6, 7, 9 ]

k=Solution()
x=k.solve(testlist,5,42950)
print x,len(x)



