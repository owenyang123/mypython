dict_sticker={'f':0,'a':0,'c':0,'e':0,'b':0,'o':0,'k':0,}
def sticker(wordstr):
    if not wordstr:
        return 0
    for i in wordstr:
        if i not in dict_sticker.keys():
            continue
        dict_sticker[i]+=1
    if dict_sticker['o'] % 2==1:
        dict_sticker['o']=dict_sticker['o']/2 + 1
    else:
        dict_sticker['o'] = dict_sticker['o'] / 2
    list_num=[]
    for i in dict_sticker.keys():
        list_num.append(dict_sticker[i])
    list_num.sort()
    return list_num[-1]

def worklist(wordlist):
    dict_list={}
    for i in wordlist:
        temp=sorted(list(i))
        temp_str="".join(temp)
        if temp_str in dict_list.keys():
            dict_list[temp_str].append(i)
        else:
            print 2,i
            dict_list[temp_str]=[i]
    list_all=[]
    for i in dict_list.keys():
        list_all.append(dict_list[i])
    return list_all



