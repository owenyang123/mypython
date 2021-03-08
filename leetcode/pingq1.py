s="A good sorting algorithm"
import collections
def tolist(s):
    res=[i.lower() for i in s if i.isalpha()]
    return sorted("".join(res))
def newstring(list1):
    counter=collections.Counter(list1)
    res="".join(sorted(list(set(list1))))
    temp=0
    for i in counter:
        if counter[i]==0:continue
        counter[i]-=1
        temp+=counter[i]
    if temp==0:return res
    nextstr=""
    for i in counter:
        nextstr+=i*counter[i]
    return res+newstring(sorted(nextstr))
def rdstr(s):
    if not s :return ""
    if len(s)==1:return s
    s=s+"."
    res,i,j="",0,1
    while(j<len(s)):
        if s[i]!=s[j]:
            res+=s[i]
            j+=1
            i=j-1
        else:j+=1
    return res
print(rdstr(newstring(tolist(s))))
result="adghilmnorstagiortgo"


def rearrangedString(s):
    s = "".join([c.lower() for c in s if c.isalpha()])
    return job(s)

def job(s):
    res, rest, set1 = "", "", set()
    if len(s)==1:return s
    for c in s:
        if c not in set1:
            set1.add(c)
            res += c
        else:
            rest += c
    res = "".join(sorted(res))
    if rest!="":return res+job(rest)
    return res
print(rearrangedString(s))