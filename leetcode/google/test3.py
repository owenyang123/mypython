def matchornot(s1,s2):
    i1,i2,l1,l2=0,0,len(s1),len(s2)
    while i1<l1 and i2<l2:
        if s1[i1]==s2[i2]:
            i1+=1
            i2+=1
        else:i1+=1
    if i2>=l2:return True
    return False

print(matchornot("abcde","bca"))