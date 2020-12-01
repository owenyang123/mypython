def rm2str(str1):
    temp1, temp2 = False, 0
    res = ""
    for i in range(len(str1)):
        if not temp1:
            temp1 = str1[i]
            temp2 = 1
        elif str1[i] == str1[i - 1]:temp2 += 1
        else:
            if temp2 != 2:res += temp1 * temp2
            else:res += temp1
            temp1 = str1[i]
            temp2 = 1
    if temp2 != 2:res += temp1 * temp2
    else:res += temp1
    return str1,res

l="aazbbbcddeffffffffghh"
print rm2str(l)