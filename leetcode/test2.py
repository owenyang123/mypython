str1="abcd"
str2="efgh"
l = []
def pstr(a,b,c):
    if a=="":
        l.append(c+b)
        return
    if b=="":
        l.append(c+a)
        return
    pstr(a[1:],b,c+a[0])
    pstr(a,b[1:],c+b[0])

pstr(str1,str2,"")
print l
dict1={2:["a","b","c"],3:["d","e","f"],4:["g","h","i"],5:["j","k","l"],6:["m","n","0"],7:["p","q","r","s"],8:["t","u","v"],9:["w","x","y","z"]}
str2="7245"
s=[]
def  traver(a,c):
    if len(a)==0 or not a:
        return
    if len(a)==1:

        for i in dict1[int(a[0])]:
            s.append(c+i)
        return
    for i in dict1[int(a[0])]:
        traver(a[1:],c+i)
traver(str2,"")
print s

