s="_VLMCS._TCP.wm.com"
temp=""
for i in s:
    if i==".":temp+=" ."
    else:temp+=" "+str(hex(ord(i)))
print temp