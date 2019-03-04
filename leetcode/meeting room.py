class Solution:
    """
    @param intervals: an array of meeting time intervals
    @return: if a person could attend all meetings
    """
    def canAttendMeetings(self, intervals):
        # Write your code here
        intervals.sort(key=lambda x: x.start)
        for k in range(1, len(intervals)):
            if intervals[k-1].end > intervals[k].start:
                return False
        return True