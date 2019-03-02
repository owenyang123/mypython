class Solution:
    def searchMatrix(self, matrix, target):
        if matrix==[] or matrix==[[]]:
            return False
        len1=len(matrix)
        if target >matrix[-1][-1] or target<matrix[0][0]:
            return False
        if target==matrix[0][0] or target==matrix[-1][-1]:
            return True
        #round 1
        i = 0
        j = len(matrix) - 1
        mid = (i + j) / 2
        if j==1 and matrix[j][0]==target:
            return True
        while (i<j-1):
            if matrix[mid][0]==target:
                return True
            if matrix[mid][0]<target:
                i=mid
                mid=(i+j)/2
            elif matrix[mid][0]>target:
                j=mid
                mid = (i + j) / 2
        if j==1 and  matrix[mid][-1]< target:
            colum = mid+1
        else:
            colum=mid
        # round 2
        if target==matrix[colum][0] or target==matrix[colum][-1]:
            return True
        i = 0
        j = len(matrix[colum]) - 1
        mid = (i + j) / 2
        while (i<j-1):
            if matrix[colum][mid]==target:
                return True
            if matrix[colum][mid]<target:
                i=mid
                mid=(i+j)/2
            elif matrix[colum][mid]>target:
                j=mid
                mid = (i + j) / 2
            print mid,i,j
        return False


k=Solution()
x=[[1,2,8,10,16,21,23,30,31,37,39,43,44,46,53,59,66,68,71],[90,113,125,138,157,182,207,229,242,267,289,308,331,346,370,392,415,429,440],[460,478,494,506,527,549,561,586,609,629,649,665,683,704,729,747,763,786,796],[808,830,844,864,889,906,928,947,962,976,998,1016,1037,1058,1080,1093,1111,1136,1157],[1180,1204,1220,1235,1251,1272,1286,1298,1320,1338,1362,1378,1402,1416,1441,1456,1475,1488,1513],[1533,1548,1563,1586,1609,1634,1656,1667,1681,1706,1731,1746,1760,1778,1794,1815,1830,1846,1861]]
print x[3]
print k.searchMatrix(x,1861)






