with open("bgp summary", 'rb') as f:
    while True:
        buf = f.read(1024)
        if buf:
            print buf
        else:
            break