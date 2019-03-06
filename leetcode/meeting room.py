<<<<<<< HEAD

=======
>>>>>>> 0598fa66911ea576147b7c0fce7e63145db73963
class Solution:
    """
    @param intervals: an array of meeting time intervals
    @return: if a person could attend all meetings
    """
    def canAttendMeetings(self, intervals):
<<<<<<< HEAD
        if len(intervals)==1:
            return True
        l=[]
        for i in intervals:
            l.append(i[0])
        l.sort()
        k=[]
        for i in range(len(l)):
            for j in range(len(intervals)):
                if l[i]==intervals[j][0]:
                    k.append((intervals[j]))        
        for i in range(len(k)-1):
            if k[i][1]>k[i+1][1]:
                return False
        return True   
=======
        # Write your code here
        intervals.sort(key=lambda x: x.start)
        for k in range(1, len(intervals)):
            if intervals[k-1].end > intervals[k].start:
                return False
        return True
>>>>>>> 0598fa66911ea576147b7c0fce7e63145db73963
