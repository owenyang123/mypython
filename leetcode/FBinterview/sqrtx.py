class Solution:
    """
    @param: x: a double
    @return: the square root of x
    """

    def sqrt(self, x):
        if x >= 1:
            start, end = 1, x
        else:
            start, end = x, 1

        while end - start > 1e-10:
            mid = (start + end) / 2
            if mid * mid < x:
                start = mid
            else:
                end = mid

        return start


class Solution1:
    """
    @param x: An integer
    @return: The sqrt of x
    """

    def sqrt(self, x):
        if x < 0:
            return None

        start, end = 0, x

        # find the last number that number^2 <= x
        while start + 1 < end:
            mid = (start + end) // 2
            if mid * mid <= x:
                start = mid
            else:
                end = mid

        if end * end <= x:
            return end

        return start


class Solution2:
    # @param x : integer
    # @param n : integer
    # @param d : integer
    # @return an integer
    def pow(self, x, n, d):
        if x == 0 and n == 0:
            return 0
        if n == 0:
            return 1 % d
        c = x % d
        if x == 1:
            return 1 % d
        if n == 1:
            return c
        print n
        if n % 2 == 0:
            return (self.pow(c, n / 2, d) * self.pow(c, n / 2, d)) % d
        else:
            return (self.pow(c, n / 2, d) * self.pow(c, n / 2, d) * x) % d

k=Solution2()
print k.pow(71045970,41535484,64735492)


int quick(int a,int b,int c)
    {
        int A=1;   //结果的保存，就是An，初始化一下
        T=a%c;     //首先计算T0的值，用于Tn的递推
        while(b!=0)
        {
          //这个if是判断目前最右边的一位bn是不是1，如果是1，那么Kn=Tn直接用Tn递推，具体看上面原理，如果bn=0,那么Kn=1,考虑到An-1是小于c的，所以 An=（An-1）%c =An-1 就是说可以不用计算了 因为相当于直接 A=A
       if(b&1) {
           A = ( A * T ) % c;
       }
       b>>=1;       //二进制位移，相当于从右到左读取位b0 b1 b2 b3 b4等等
       T=(T*T)%c;   //更新T，如果下一位是1就可以用这个算A，具体的可以看上面原理的递推关系
   }
   return A;
————————————————
版权声明：本文为CSDN博主「Liiiiiiiiiiiiiiiiiiq」的原创文章，遵循 CC 4.0 BY-SA 版权协议，转载请附上原文出处链接及本声明。
原文链接：https://blog.csdn.net/qq_36760780/article/details/80092665