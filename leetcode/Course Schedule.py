class Solution:

    def canFinish(self, numCourses, prerequisites):
        edges = {i:[] for i in range(numCourses)}
        degrees = [0] * numCourses
        for i, j in prerequisites:
            edges[j].append(i)
            degrees[i] += 1
        queue = collections.deque([])
        for k in range(numCourses):
            if degrees[k] == 0:
                queue.append(k)
        count = 0
        while queue:
            course = queue.popleft()
            count += 1
            for pair in edges[course]:
                degrees[pair] -= 1
                if degrees[pair] == 0:
                    queue.append(pair)
        return True if count == numCourses else False