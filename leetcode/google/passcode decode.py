def decryptPassword(s):
    len1=len(s)
    flag_allnum=True
    for i in s:
        if i.isalpha():
            flag_allnum=False
            break
    if flag_allnum:
        return s[0:len1/2][::-1]
    while (s[0].isdigit()):
        s=s[::-1].replace("0",s[0],1)[::-1][1:]
    len1=len(s)
    list1=[]
    i=0
    s=s[::-1]
    while(i<len1):
        if i<=len1-3 and s[i]=="*" and s[i+1].islower() and s[i+2].isupper():
            list1.append(s[i+2])
            list1.append(s[i+1])
            i+=3
        else:
            list1.append(s[i])
            i+=1
    print list1
    return "".join(list1[::-1])

print  3^4
call 