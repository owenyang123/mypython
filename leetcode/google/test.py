import collections
import re,copy


<<<<<<< HEAD
with open("piclog",'r') as x:
    #print x.read().split("\n")
=======

with open("piclog") as x:
>>>>>>> c62e426afd51e1938a055f5d0c530bbb4980021c
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(5)[0][0]

