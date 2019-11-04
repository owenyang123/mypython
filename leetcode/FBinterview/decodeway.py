def helper(instring,strlen):
    if strlen==0 or strlen==1:
        return 1
    if strlen==2 and int(instring)<27:
        return 2
    s=len(instring)-strlen
    result=helper(instring[s+1:],strlen-1)
    if strlen>2 and int(instring[s:s+2])<27 :
        result+=helper(instring,strlen-2)
    return result

def decodeways(instring):
    if not instring:return 0
    if len(instring)==1:return 1
    if instring[0]=="0":
        return decodeways(instring[1:])
    str123=instring[0]
    for i in range(1,len(instring)):
        if instring[i]=="0" and instring[i-1]=="0":
            continue
        str123+=instring[i]
    return helper(str123,len(str123))

print  decodeways("111111111111111111111111111111111111111111111111111111111111")