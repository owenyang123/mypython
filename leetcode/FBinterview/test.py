import re

print  re.sub(r'(.)\1*', lambda m: str(len(m.group(0))) + m.group(1), "9999999999999999999999213131232")