import re
s = 'aaa@xxx.com bbb@yyy.com ccc@zzz.com'
print re.sub('([a-z]*)@', r'\1-123@', s)