def product(*argus):
    if not argus:
        return "fail"
    k=1
    for i in argus:
       k=k*i
    return k
print product()