<<<<<<< HEAD
import collections
class Solution(object):
    def ladderLength(self, beginWord, endWord, wordList):
        wordList = set(wordList)
        queue = collections.deque([[beginWord, 1]])
        while queue:
            word, length = queue.popleft()
            if word == endWord:
                return length
            for i in range(len(word)):
                for c in 'abcdefghijklmnopqrstuvwxyz':
                    next_word = word[:i] + c + word[i+1:]
                    if next_word in wordList:
                        wordList.remove(next_word)
                        queue.append([next_word, length + 1])
        return 0
k=Solution()
print k.ladderLength("qa","sq",["si","go","se","cm","so","ph","mt","db","mb","sb","kr","ln","tm","le","av","sm","ar","ci","ca","br","ti","ba","to","ra","fa","yo","ow","sn","ya","cr","po","fe","ho","ma","re","or","rn","au","ur","rh","sr","tc","lt","lo","as","fr","nb","yb","if","pb","ge","th","pm","rb","sh","co","ga","li","ha","hz","no","bi","di","hi","qa","pi","os","uh","wm","an","me","mo","na","la","st","er","sc","ne","mn","mi","am","ex","pt","io","be","fm","ta","tb","ni","mr","pa","he","lr","sq","ye"])
=======

from jnpr.junos import Device
import threading
from lxml import etree
import datetime

list1=["ashburn.ultralab.juniper.net","asterix.ultralab.juniper.net","automatix.ultralab.juniper.net","beltway.ultralab.juniper.net","bethesda.ultralab.juniper.net","botanix.ultralab.juniper.net","cacofonix.ultralab.juniper.net","dogmatix.ultralab.juniper.net","erebus.ultralab.juniper.net","getafix.ultralab.juniper.net","greece.ultralab.juniper.net","holland.ultralab.juniper.net","hypnos.ultralab.juniper.net","idefix.ultralab.juniper.net","kratos.ultralab.juniper.net","matrix.ultralab.juniper.net","moros.ultralab.juniper.net","nyx.ultralab.juniper.net","obelix.ultralab.juniper.net","pacifix.ultralab.juniper.net","photogenix.ultralab.juniper.net","rio.ultralab.juniper.net","timex.ultralab.juniper.net"]
dict1={}
def listhw(str1):
    if not str1:return None
    global dict1
    try:
        dev = Device(host = str1, user='labroot', password='lab123')
        dev.open()
        x=dev.rpc.get_chassis_inventory()
        dev.close()
        head=etree.tostring(x).split("\n")
        temp=[str1]
        for i in head:
            if "description" in i:
                temp_str=i.replace("<"," ").replace(">"," ")
                if ("DPC" in temp_str or "MPC" in temp_str or "RE"in temp_str) and "PMB" not in temp_str:
                    if i[13]=="M" or i[13]=="D" or i[13]=="R":temp.append(i[13:-14])
        dict1[temp[0]]=list(set(temp[1:]))
    except:
        pass
    return
instance=[]
for i in list1:
    trd=threading.Thread(target=listhw,args=(i,))
    trd.start()
    instance.append(trd)
for thread in instance:
    thread.join()
temp=[]
for  i in dict1:
    temp.append([i]+sorted(dict1[i]))
temp.sort(key=lambda a:a[0])
for i in temp:
    print i
>>>>>>> bd0b7fa129262ff7e84455e5bc7ada8bd15f877a
