def genin(x1,x2):
    return 2**(sum([1 for i in x1 if i not in set(x2)]))

print genin('WxYZ','wXyZ')