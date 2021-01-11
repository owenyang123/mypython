import collections

print collections.Counter([1,2,3,4,1,1,1,1,5,100,200,4,4,4,4]).most_common(1)[0][0]