def helper(data,k,memo):
    if k==0:
        return 1
    s=len(data)-k
    if data[s]=="0" :
        return 0
    if memo[k]!=None:
        return memo[k]
    result=helper(data,k-1,memo)
    if k>=2 and int(data[s:s+2])<=26:
        result += helper(data, k - 2,memo)
    return result

def numways(data):
    memo=[None]*(len(data)+1)
    return helper(data,len(data),memo)


print numways("123423000100")