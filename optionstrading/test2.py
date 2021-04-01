# import basictools as bt
# import pymysql
# import pandas as pd
# import time
# import matplotlib.pyplot as plt
# con = pymysql.connect(host='localhost',
#                       user='owenyang',
#                       password='222121wj',
#                       db='stock',
#                       charset='utf8mb4',
#                       cursorclass=pymysql.cursors.DictCursor)
# frame = pd.read_sql("select * from stock.realdata where Stocksymbol='AMD'",con).set_index('Date')
# frame.index = pd.to_datetime(frame.index)
# list1=[]
# for ind in frame.index:
#     list1.append([ind,frame['Prices'][ind]])
# dict1,sum={},0
# for i in range(len(list1)):
#     sum+=list1[i][1]
#     if i>=50:
#         sum-=list1[i-50][1]
#         dict1[list1[i][0]]=sum/50.00
# frame2=pd.DataFrame.from_dict(dict1,orient='Index', columns=['Prices'])
# x=pd.concat([frame, frame2], axis=1)
# x.plot(subplots=False, figsize=(10, 4))
# plt.show()
#
#

class Solution(object):
    def minimumEffortPath(self, heights):
        if not heights: return 0
        # if len(heights)==1:
        #     temp=0
        #     for i in range(1,len(heights[0])):
        #         temp=max(temp,abs(heights[0][i]-heights[0][i-1]))
        #     return temp
        rows, clos = len(heights), len(heights[0])
        self.b = [[0 for x in range(clos)] for y in range(rows)]
        dict1 = {}
        for i in range(rows):
            for j in range(clos):
                self.b[i][j] = heights[i][j]
                dict1[(i, j)] = [(i, j)]
                if i + 1 < rows: dict1[(i, j)].append((i + 1, j))
                if i - 1 >= 0: dict1[(i, j)].append((i - 1, j))
                if j + 1 < clos: dict1[(i, j)].append((i, j + 1))
                if j - 1 >= 0: dict1[(i, j)].append((i, j - 1))
                dict1[(i, j)].pop(0)
        self.l = float('inf')
        self.dfsroute(dict1, (rows - 1, clos - 1), [(0, 0)], 0, rows * clos)
        return self.l

    def dfsroute(self, topology, end, temppath, num, num1):
        if len(temppath) > num1 and end != temppath[-1]:
            return
        if end == temppath[-1]:
            self.l = min(self.l, num)
            return
        for i in topology[temppath[-1]]:
            if i in set(temppath): continue
            self.dfsroute(topology, end, temppath + [i],
                          max(num, abs(self.b[temppath[-1][0]][temppath[-1][1]] - self.b[i[0]][i[1]])), num1)
        return
import re
def availab_set(nums,sitornot):
    temp=[i[0]*i[1] for i in zip(nums,sitornot)]
    if not temp:return []
    if sum(temp)==0:return []
    left=0
    for i in range(len(temp)):
        if temp[i]==0:continue
        left=i
        break
    right=left+1
    res=[]
    while(right<len(temp)):
        if temp[left]==0:
            left+=1
            right+=1
            continue
        elif temp[right]==0:
            res.append([temp[left], temp[right - 1]])
            left=right+1
            right=left+1
        else:
            right+=1
    if temp[-1]!=0:res.append([temp[left], temp[-1]])
    return [i for i in res if i[0]!=i[-1]]



list1=range(1,11)
list2=[1,1,0,1,1,1,1,1,1,1]

print(availab_set(list1,list2))
