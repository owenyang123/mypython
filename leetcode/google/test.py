import collections
import re


words = re.findall(r'\w+', "i am a boy boy boy Aaa")
print type(words)

print collections.Counter(words).most_common(3)