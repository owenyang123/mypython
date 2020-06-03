import collections
import re,copy


l=[1,2,3,4,6]

with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(5)[0][0]

