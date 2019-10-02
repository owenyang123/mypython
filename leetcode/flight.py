import sys
class Solution:
    def findCheapestPrice(self, n, flights, src, dst, K):
        distance = [sys.maxsize for i in range(n)]
        distance[src] = 0
        print distance

        for i in range(0, K + 1):
            dN = list(distance)
            for u, v, c in flights:
                dN[v] = min(dN[v], distance[u] + c)
            distance = dN
            print dN

        if distance[dst] != sys.maxsize:
            return distance[dst]
        else:
            return -1

k=Solution()

print k.findCheapestPrice(4,[[0,1,100],[1,2,100],[0,2,500],[2,3,500]],0,2,1)