import collections
import re,copy



with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(5)[0][0]

