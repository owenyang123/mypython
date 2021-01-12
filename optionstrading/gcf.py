def gcf(a,b):
    if a<=0 or b<=0:return 0
    if a==b:return b
    x,y=min(a,b),max(a,b)
    t=y-x
    if y%t==0 and x%t==0:return t
    return gcf(x,t)
def lcm(a,b):
    x=gcf(a,b)
    return (a*b)/x

print lcm(27,42)