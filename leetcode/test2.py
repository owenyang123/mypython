def getlast(str1,x):
    if len(str1)==0:
        return 1
    elif len(str1)==1:
        x=str1
        return x
    else:
        return getlast(str1[1:],x)

x=getlast("13123123123213213sdadadad","")
print x