"""
The knows API is already defined for you.
@param a, person a
@param b, person b
@return a boolean, whether a knows b
you can call Celebrity.knows(a, b)
"""


class Solution:
    # @param {int} n a party with n people
    # @return {int} the celebrity's label or -1
    def findCelebrity(self, n):
        celeb = 0

        for i in range(1, n):
            if Celebrity.knows(celeb, i):
                celeb = i

        for i in range(n):
            if celeb != i and Celebrity.knows(celeb, i):
                return -1
            if celeb != i and not Celebrity.knows(i, celeb):
                return -1

        return celeb