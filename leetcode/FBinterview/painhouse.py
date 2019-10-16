class Solution:
    """
    @param costs: n x k cost matrix
    @return: an integer, the minimum cost to paint all houses
    """

    def minCostII(self, costs):
        # write your code here

        if not costs or len(costs) == 0:
            return 0

        m, k = len(costs), len(costs[0])
        res = [0 for _ in range(k)]

        for i in range(m):
            # find the min and 2nd min
            # ...
            fir_min, sec_min, min_index = sys.maxsize, sys.maxsize, 0
            for j in range(k):
                if res[j] < fir_min:
                    sec_min = fir_min
                    fir_min = res[j]
                    min_index = j
                else:
                    if res[j] < sec_min:
                        sec_min = res[j]

            for j in range(k):
                if j == min_index:
                    res[j] = sec_min + costs[i][j]
                else:
                    res[j] = fir_min + costs[i][j]
        return min(res)