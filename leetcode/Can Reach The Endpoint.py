class Solution:
    """
    @param map: the map
    @return: can you reach the endpoint
    """
    def reachEndpoint(self, map):
        if map[0][0]==0:
            return False
        x1=0
        y1=0
        for i in range(len(map)):
            for j in range(len(map[0])):
                if map[i][j]==9:
                    x1=i
                    y1=j
                    break
                elif i==0 and j==0:
                    pass
                elif i==0 and j!=0:
                    if map[0][j-1]==0:
                        map[0][j]=0
                    else:
                        map[0][j]=min(map[0][j-1],map[0][j])
                elif i!=0 and j==0:
                    if map[i-1][j]==0:
                        map[i][0]=0
                    else:
                        map[i][0]=min(map[i-1][0],map[i][0])
                else:
                    if map[i][j]!=0:
                        map[i][j]=max(map[i-1][j],map[i][j-1])
        print x1,y1,map
        if map[x1-1][y1]==1 or map[x1][y1-1]==1:
            return True
        return False