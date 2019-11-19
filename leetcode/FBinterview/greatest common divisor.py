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


class Solution1:
	# @param A : integer
	# @param B : integer
	# @return an integer
	def cpFact(self, A, B):
		if A == 0: return -1
		if A == 1 or B == 1: return 1
		for i in self.getf(A):
			if A % i == 0 and self.gcd(i, B) == 1:
				return int(i)
		return -1

	def getf(self, A):
		l = [1, A]
		for i in range(2, int(A ** 0.5) + 1):
			if A % i == 0:
				l.append(i)
				l.append(A / i)
		l.sort(reverse=True)
		return l

	def gcd(self, A, B):
		if A < B: return self.gcd(B, A)
		if B == 1: return 1
		if B == 0: return A
		if A % B == 0: return B
		return self.gcd(B, A % B)