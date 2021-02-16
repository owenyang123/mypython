def whereisnow(str1, str2):
    if not str2:return str1
    if str2.startswith("/"):temp=str2
    else:temp=str1+"/"+str2
    stack=[]
    for cmd in temp.split("/"):
        if stack and cmd == "..":stack.pop()
        elif cmd not in [".", "", ".."]:stack.append(cmd)

    return "/" + "/".join(stack)

print whereisnow("/a/b","/../x")