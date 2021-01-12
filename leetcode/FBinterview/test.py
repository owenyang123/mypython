import collections
import re
class Solution:
    # @param A : tuple of integers
    # @return an integer
    def repeatedNumber(self, A):
        if not A:
            return -1
        if len(A)<=2:
            return A[0]
        num=len(A)/3
        counterlist=collections.Counter(A)
        for i in counterlist:
            if counterlist[i]>num:
                return i
        return -1


k=Solution()
print k.repeatedNumber([ 1000441, 1000441, 1000994 ])

str1="case  case case        owen       123" \
     "131312 123123" \
     "13131 123123 owen owen " \
     "wjing " \
     "ge-0/0/0" \
     "1000" \
     "200"
l=re.findall(r'\w+',str1)
print l