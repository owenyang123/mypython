"""
Definition of ListNode
class ListNode(object):
    def __init__(self, val, next=None):
        self.val = val
        self.next = next
"""

class Solution:
    """
    @param head: 
    @return: nothing
    """
    def countNodesII(self, head):
        if not head:
            return 0
        if head.next==None:
            return 0
        temp=head
        len=0
        while temp!=None:
            if temp.val>0:
                len=len+1
            temp=temp.next
        return len
