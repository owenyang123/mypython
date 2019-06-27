class Solution:
    def findMissing2(self, n, str):
        dict1=self.help(n)
        dict2={0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0}
        for i in str:
            dict2[int(i)]+=1
        l=[]
        for i in range(10):
            if (dict1[i]-dict2[i])!=0:
                l.append(i)
            if (dict1[i]-dict2[i])==2:
                 l.append(i)
        l.sort()
        print l
        if len(l)==1:
            return l[0]
        a=10*l[0]+l[1]
        b=10*l[1]+l[0]
        if b>n:
            return a
        if a>n:
            return b
        c=self.InttoString(a)
        str_tmp="i"
        for i in c:
            str_tmp=str_tmp+i
        print  str_tmp[1::]
        if str_tmp[1::] not in str:
            return a
        else:
            return b

    def help(self, n):
        dict1={0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0}
        if n<10:
            for i in range(1,n+1):
                dict1[i]=1+dict1[i]
        if n==10:
            dict1=self.help(9)
            dict1[1]=dict1[1]+1
            dict1[0] = dict1[0] + 1
        if n>10 and n<20:
            dict1=self.help(10)
            for i in range (11,n+1):
                dict1[i-10]+=1
                dict1[1]+=1
        if n==20:
            dict1=self.help(19)
            dict1[2]+=1
            dict1[0]+=1
        if n>20 and n<30:
            dict1=self.help(20)
            for i in range(21, n+1):
                dict1[i - 20] += 1
                dict1[2] += 1
        if n==30:
            dict1 = self.help(29)
            dict1[3]+=1
            dict1[0]+=1
        return dict1
    def InttoString(self, x):
        return str(x)