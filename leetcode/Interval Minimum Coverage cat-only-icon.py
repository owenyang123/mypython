"""
Definition of Interval.
class Interval(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
"""

class Solution:
    """
    @param a: the array a
    @return: return the minimal points number
    """
    def getAns(self, a):
        if not a:
            return 0
        aa=[]
        dict1={}
        for i in a:
            if i.start not in dict1.keys():
                aa.append([i.start,i.end])
                dict1[i.start]=i.end
            else:
                dict1[i.start]=max(dict1[i.start],i.end)
        aa.sort(key=lambda x:x[0])
        for i in range(len(aa)):
            aa[i][1]=dict1[aa[i][0]]
        l=[]
        i=0
        j=1
        while(i<=len(aa)-1 and j<=len(aa)-1):
            if i==len(aa)-1:
                l.append(aa[i])
                i=i+1
            elif j==len(aa)-1:
                if aa[i][1]>aa[j][0]:
                    l.append([aa[i][0],aa[j][1]])
                    j=j+1
                    i=j
                else:
                    l.append([aa[i][0],aa[j-1][1]])
                    i=j
            elif aa[i][1]<aa[j][0]:
                l.append([aa[i][0],aa[j-1][1]])
                i=j
                j=j+1
            else:
                j=j+1
        print l
        return len(l)
