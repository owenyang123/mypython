class Solution:

    def insert(self, intervals, new_interval):
        new_interval.start, new_interval.end = min(new_interval.start, new_interval.end), max(new_interval.start,
                                                                                              new_interval.end)
        intervals.append(new_interval)
        intervals = sorted(intervals, key=lambda x: x.start)
        cur = intervals[0]
        res = []
        for i in range(1, len(intervals)):
            if cur.end >= intervals[i].start:
                cur.end = max(intervals[i].end, cur.end)
            else:
                res.append(cur)
                cur = intervals[i]
        res.append(cur)
        return res

        return intervals