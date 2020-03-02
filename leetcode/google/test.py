import collections
import re,copy


with open("piclog",'r') as x:
    #print x.read().split("\n")
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(5)

print ("abc" in "adaddabcadadad")