class Solution:
    # @param A : string
    # @return a strings
    def solve(self, A):
        s=""
        for i in range(len(A)-1):
            if A[i]==" " and A[i+1]==" ":
                continue
            s+=A[i]
        if A[-1]!=" ":
            s+=A[-1]
        l=s.split(" ")
        l.reverse()
        return " ".join(l)
k=Solution()
print k.solve("            i am working for juniper networks as JTAC                 engineer                ")

