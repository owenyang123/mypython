#Given a set of non-overlapping intervals, insert a new interval into the intervals (merge if necessary).
#You may assume that the intervals were initially sorted according to their start times.
#Example 1:
#Given intervals [1,3],[6,9] insert and merge [2,5] would result in [1,5],[6,9].


class Interval:
    def __init__(self, s=0, e=0):
        self.start = s
         self.end = e

class Solution:

    def insert(self, intervals, new_interval):
        new_interval.start,new_interval.end=min(new_interval.start,new_interval.end),max(new_interval.start,new_interval.end)
        intervals.append(new_interval)
        intervals = sorted(intervals, key=lambda x: x.start)
        cur = intervals[0]
        res = []
        for i in range(1, len(intervals)):
            if cur.end >= intervals[i].start:
                cur.end = max(intervals[i].end, cur.end)
                continue
            res.append(cur)
            cur = intervals[i]
        res.append(cur)
        return res
