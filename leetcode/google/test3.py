def nest(list1):
    if not list1:return []
    def dfs(list2,temp):
        if not list2:return temp
        for i in list2:
            if type(i).__name__=='list':
                temp=dfs(i,temp)
            else:temp+=[i]
        return temp
    res=dfs(list1,[])
    return res
print(nest([1,2,3,[4,5,[99,100]]]))

