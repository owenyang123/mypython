l=[]
def allipaddress(ipstr,temp,n):
    if n==0:
        l.append(temp+ipstr)
        print l
        n=2
        return
    else:
        for i in range(1,4):
            if temp=="":
                temp=ipstr[0:i]+"."
                n=n-1
                print ipstr[i:],n,temp,"xx"
                allipaddress(ipstr[i:], temp, n)
            else:
                temp=temp+ipstr[0:i]+"."
                n=n-1
                print ipstr[i:],n,temp
                allipaddress(ipstr[i:], temp, n)

allipaddress("111222333444","",3)
print l