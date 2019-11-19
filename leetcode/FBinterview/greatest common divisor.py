class Solution:
	# @param A : integer
	# @param B : integer
	# @return an integer
	def gcd(self, A, B):
	    if A<B:return self.gcd(B,A)
	    if B==1:return 1
	    if B==0:return A
	    if A%B==0:return B
	    return self.gcd(B,A%B)