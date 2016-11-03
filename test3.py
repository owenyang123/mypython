import numpy as np
shape=1
s='civilwartestingwhetherthatnaptionoranynartionsoconceivedandsodedicatedcanlongendureWeareqmetonagreatbattlefiemldoftzhatwarWehavecometodedicpateaportionofthatfieldasafinalrestingplaceforthosewhoheregavetheirlivesthatthatnationmightliveItisaltogetherfangandproperthatweshoulddothisButinalargersensewecannotdedicatewecannotconsecratewecannothallowthisgroundThebravelmenlivinganddeadwhostruggledherehaveconsecrateditfaraboveourpoorponwertoaddordetractTgheworldadswfilllittlenotlenorlongrememberwhatwesayherebutitcanneverforgetwhattheydidhereItisforusthelivingrathertobededicatedheretotheulnfinishedworkwhichtheywhofoughtherehavethusfarsonoblyadvancedItisratherforustobeherededicatedtothegreattdafskremainingbeforeusthatfromthesehonoreddeadwetakeincreaseddevotiontothatcauseforwhichtheygavethelastpfullmeasureofdevotionthatweherehighlyresolvethatthesedeadshallnothavediedinvainthatthisnationunsderGodshallhaveanewbirthoffreedomandthatgovernmentofthepeoplebythepeopleforthepeopleshallnotperishfromtheearth'
s1=[]
s2=[]
for i in range( len(s)):
    s1.append(s[i])
    s2.append(1)
for i in range(len(s1)-1):
    t3=min(i,(len(s1)-i))
    if s1[i-1]==s1[i+1] and i-1>=0 :
        shape=shape+2
        tmp=0
        for k in range(1,t3):
            if i+k+1<=len(s1)-1 and i-k-1>=0:
                if s1[i-k-1]==s1[i+k+1]  :
                    tmp=tmp+1
                else:
                    break
        shape=shape+2*tmp
        tmp=0
        s2[i]=shape
        shape=1
k2=np.array(s2)
tmp=np,max(k2)
for i in range(len(s2)):
    if s2[i]==tmp[1]:
        index=i
        print s1[index-s2[index]/2:index+1+s2[index]/2]



