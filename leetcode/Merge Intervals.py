class Interval:
     def __init__(self, s=0, e=0):
         self.start = s
         self.end = e

class Solution:

    def insert(self, intervals, new_interval):
        new_interval.start, new_interval.end = min(new_interval.start, new_interval.end), max(new_interval.start,new_interval.end)
        if new_interval.end < intervals[0].start:
            intervals.insert(0, new_interval)
            return intervals
        elif new_interval.start > intervals[-1].end:
            intervals.append(new_interval)
            return intervals
        else:
            l=[]
            i,j=0,0
            fix=0
            while (j<=len(intervals)-1):
                if new_interval.start>intervals[i].end:
                    l.append(intervals[i])
                    if new_interval.start<=intervals[i+1].start:
                        fix=1
                        intervals[i + 1].start=new_interval.start
                    i=i+1
                    j=i
                elif new_interval.start>intervals[i].start and  new_interval.start<=intervals[i].end:
                    fix=1
                elif fix==1 and (new_interval.end<=intervals[j].end):
                    class1=Interval()
                    class1.start=intervals[i].start
                    class1.end = intervals[j].end
                    l.append(class1)
                    j+=1
                    break
                elif fix==1 and (new_interval.end>intervals[j].end and new_interval.end<intervals[j+1].start):
                    class1=Interval()
                    class1.start=intervals[i].start
                    class1.end = new_interval.end
                    l.append(class1)
                    j+=1
                    break
                elif fix==1:
                    j+=1
            for z in range(j,len(intervals)):
                l.append(intervals[i])
            return l