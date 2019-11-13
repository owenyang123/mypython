class Solution:
    # @param A : list of integers
    # Modify the array A which is passed by reference.
    # You do not need to return anything in this case.
    def arrange(self, A):
        l=[]
        for i in range(len(A)):
            l.append(A[A[i]])
        for i in range(len(A)):
            A[i]=l[i]
        return A