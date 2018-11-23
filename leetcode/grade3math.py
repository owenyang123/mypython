for a in range(0,10):
    for b in range(0,10):
        for c in range(0, 10):
            x=100*a+10*b+c
            y=100*c+10*a+b
            if (x==2*y) or (y==2*x):
                print x,y


