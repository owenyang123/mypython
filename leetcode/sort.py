l=[5,4,3,6,7.99,18,100,101,102,103,1040000,11,12,13,1000]
def bubble(arr):
    def swap(i,j):
        arr[i],arr[j]=arr[j],arr[i]
    n=len(arr)
    swapped=True
    x=-1
    while swapped :
        swapped=False
        x=x+1
        for i in range(1,n-x):
            if arr[i-1]>arr[i]:
                swap(i-1,i)
                swapped=True
    return arr

sor
print bubble(l)
s="A"

print s.islower()
