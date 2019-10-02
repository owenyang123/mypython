class Solution:
    # @param A : list of integers
    # @return an integer
    def maxArr(self, A):
        k=len(A)
        l=[]
        for i in range(k):
            temp=[i,A[i],A[i]-i]
            l.append(temp)
        l.sort(key=lambda l:l[0])
        cur1=0
        for i in l:
            cur1 = max(cur1,abs(i[0]-l[0][0])+abs(i[1]-l[0][1]))
        l.sort(key=lambda l:l[1])
        cur2=0
        for i in l:
            cur2= max(cur2,abs(i[0]-l[0][0])+abs(i[1]-l[0][1]))
        l.sort(key=lambda l: l[2])
        cur3 = 0
        for i in l:
            cur3 = max(cur2, abs(i[0] - l[0][0]) + abs(i[1] - l[0][1]))
        cur=max(cur1,cur2,cur3)
        return cur

k=Solution()
print k.maxArr( [  -54, 84, -88, 30, 65, -66, 17, -68, -40, 42, 0, -43, -33, -60, 85, -94, 43, -18, 86, -81, -30, 3, 32, -50, 94, -96, -9, -82, 3, -62, 23, -50, 86, -36, -62, 8, 51, 34, 1, -2, -25, -37, 82, 17, -10, 60, -61, -71, -56, 19 ] )