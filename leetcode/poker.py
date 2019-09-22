class Solution:
    """
    @param cards:
    @return: the minimal times to discard all cards
    """

    def getAns(self, cards):
        cards.sort()
        list1 = list(set(cards))
        dict1 = {}
        for i in cards:
            if i not in dict1.keys():
                dict1[i] = 1
            else:
                dict1[i] += 1
        k = [[0, 0]]
        x = 0
        for i in range(len(list1) - 1):
            if list1[i + 1] - list1[i] == 1:
                k[x][0] = i
                k[x][1] += 1
            else:
                k.append([i, 0])
                x += 1
        round = 0
        for i in k:
            if i[1] >= 4:
                for j in range(i[0] + 1 - i[1], i[1] + 2):
                    if j in dict1.keys() and dict1[j] > 0:
                        dict1[j] -= 1
                round += 1
        for i in dict1.keys():
            if dict1[i] >= 2:
                round += 1
                dict1[i] = 0
        for i in dict1.keys():
            if dict1[i] == 1:
                round += 1
                dict1[i] = 0

        return round