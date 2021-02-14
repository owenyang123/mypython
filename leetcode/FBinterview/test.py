import re
s = '221112233112321'

m=re.search(r'(.)\1{2}',s)
print m.group(0)