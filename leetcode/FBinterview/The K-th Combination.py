class Solution:
    """
    @param n: The integer n
    @param k: The integer k
    @return: Return the combination
    """
    def getCombination(self, n, k):
        A=[]
        for i in range(1,n+1):
            A.append(i)
        if not A:
            return 0
        B=len(A)
        combinations = []
        self.dfs(A, 0, [], combinations, B)
        n = 0
        return combinations[k-1]

    def dfs(self, nums, index, combination, combinations, B):
        if len(combination) ==B/2:
            combinations.append(list(combination))

        for i in range(index, len(nums)):
            combination.append(nums[i])
            self.dfs(nums, i +1, combination, combinations, B)
            combination.pop()