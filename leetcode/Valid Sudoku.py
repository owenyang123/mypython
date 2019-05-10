class Solution(object):
    def isValidSudoku(self, board):
        """
        :type board: List[List[str]]
        :rtype: bool
        """
        dic = {}
        for i in range(len(board)):
            for j in range(len(board[0])):
                cur = board[i][j]
                if cur == ".":
                    continue
                if cur in dic:
                    for index in range(len(dic[cur])):
                        ele = dic[cur][index]
                        if ele[0] == i or ele[1] == j or (int(ele[0]) / 3 == i / 3 and int(ele[1]) / 3 == j / 3):
                            return False
                        else:
                            dic[cur].append([i, j])
                else:
                    dic[cur] = [[i, j]]
        return True