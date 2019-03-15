"""
Definition of ListNode
class ListNode(object):
    def __init__(self, val, next=None):
        self.val = val
        self.next = next
"""


class Solution:
    """
    @param head: The first node of linked list
    @param n: the start index
    @param m: the end node
    @return: A ListNode
    """

    def deleteNode(self, head, n, m):
        if not head:
            return None
        len = 0
        temp = head
        while temp.next != None:
            len = len + 1
            temp = temp.next
        if n == 0:
            cur2 = head
            for i in range(len):
                if i == m:
                    cur2 = cur2.next
                    break
                cur2 = cur2.next
            return cur2
        else:
            cur1 = head
            for i in range(len):
                if i == n - 1:
                    break
                cur1 = cur1.next
            cur2 = head
            for i in range(len):
                if i == m:
                    cur2 = cur2.next
                    break
                cur2 = cur2.next
            cur1.next = cur2
            return head


