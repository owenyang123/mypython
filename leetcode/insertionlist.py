"""
Definition of ListNode
class ListNode(object):
    def __init__(self, val, next=None):
        self.val = val
        self.next = next
"""


class Solution:
    """
    @param head: The first node of linked list.
    @return: The head of linked list.
    """

    def insertionSortList(self, head):
        if not head:
            return None
        l = []
        cur = head
        while (cur):
            l.append([cur, cur.val])
            cur = cur.next
        l.sort(key=lambda x: x[1])

        for i in range(len(l)):
            if i == len(l) - 1:
                l[i][0].next = None
            else:
                l[i][0].next = l[i + 1][0]
        return l[0][0]