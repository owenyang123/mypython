class Solution:

    def findCheapestPrice(self, n, flights, src, dst, K):
        distance = [sys.maxsize for i in range(n)]
        distance[src] = 0

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