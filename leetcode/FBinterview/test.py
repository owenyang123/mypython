def gcf(a, b):
    if b > a: return gcf(b, a)
    if a % b == 0: return b
    while (a % b != 0):
        return gcf(a - b, b)
str.startswith()

