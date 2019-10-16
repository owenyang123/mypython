class Solution:
    """
    @param rooms: m x n 2D grid
    @return: nothing
    """

    def wallsAndGates(self, rooms):
        # write your code here
        # 0 gate
        # -1 wall
        for row in range(len(rooms)):
            for col in range(len(rooms[0])):
                if rooms[row][col] != 0:
                    continue
                self.bfs(rooms, row, col)

    def bfs(self, rooms, row, col):
        dir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        visited = set([(row, col)])
        cur_state = (row, col, 0)
        import queue
        que = queue.Queue()
        que.put(cur_state)
        while not que.empty():
            cur_row, cur_col, cur_step = que.get()
            if rooms[cur_row][cur_col] < cur_step:
                continue
            rooms[cur_row][cur_col] = cur_step
            next_step = cur_step + 1
            for (drow, dcol) in dir:
                next_row, next_col = cur_row + drow, cur_col + dcol
                if next_row < 0 or next_row >= len(rooms) or next_col < 0 or next_col >= len(rooms[0]):
                    continue
                if rooms[next_row][next_col] == -1 or rooms[next_row][next_col] == 0:
                    continue
                if (next_row, next_col) in visited:
                    continue
                visited.add((next_row, next_col))
                que.put((next_row, next_col, next_step))