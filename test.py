import numpy as np
shape=1
s='civilwartestingwhetherthatnaptionoranynartionsoconceivedandsodedicatedcanlongendureWeareqmetonagreatbattlefiemldoftzhatwarWehavecometodedicpateaportionofthatfieldasafinalrestingplaceforthosewhoheregavetheirlivesthatthatnationmightliveItisaltogetherfangandproperthatweshoulddothisButinalargersensewecannotdedicatewecannotconsecratewecannothallowthisgroundThebravelmenlivinganddeadwhostruggledherehaveconsecrateditfaraboveourpoorponwertoaddordetractTgheworldadswfilllittlenotlenorlongrememberwhatwesayherebutitcanneverforgetwhattheydidhereItisforusthelivingrathertobededicatedheretotheulnfinishedworkwhichtheywhofoughtherehavethusfarsonoblyadvancedItisratherforustobeherededicatedtothegreattdafskremainingbeforeusthatfromthesehonoreddeadwetakeincreaseddevotiontothatcauseforwhichtheygavethelastpfullmeasureofdevotionthatweherehighlyresolvethatthesedeadshallnothavediedinvainthatthisnationunsderGodshallhaveanewbirthoffreedomandthatgovernmentofthepeoplebythepeopleforthepeopleshallnotperishfromtheearth'
s1=[]
s2=[]
for i in range( len(s)):
    s1.append(s[i])
    s2.append(1)
half=len(s1)/2
for i in range(half):
    t3=min(i,(half-i))
    tmp=0
    if s1[i-1]==s1[i+1] and i-1>=0 :
        shape=shape+2
        tmp=0
        for k in range(1,t3):
            if s1[i-k-1]==s1[i+k+1] and i-k-1>=0 :
                tmp=tmp+1
            else:
                break
        shape=shape+2*tmp
        tmp=0
        s2[i]=shape
        shape=1
for i in range(half,len(s1)-1):
    t3=min(i-half,len(s1)+1-i)
    tmp=0
    if s1[i-1]==s1[i+1]:
        shape=shape+2
        tmp=0
        for k in range(1,t3):
            if s1[i-k-1]==s1[i+k+1] and i-k-1>=half and i+k+1<=len(s)+1 :
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
        print s1,len(s1)
        print s2,len(s2)
        print tmp[1]
        print index
        print s1[index-tmp[1]/2:index+1+tmp[1]/2]



