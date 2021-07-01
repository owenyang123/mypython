import re
with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print(words)