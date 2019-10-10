class Solution:
    """
    @param head: The first node of linked list.
    @return: True if it has a cycle, or false
    """
    def hasCycle(self, head):
        if not head:
            return False
        if head.next==head:
            return True
        dict1={}
        while head.next!=None:
            if head.val in dict1.keys() and head.next==dict1[head.val][1]:
                return True
            else:
                dict1[head.val]=[head.val,head.next]
                head=head.next
        return False


class Solution:
    """
    @param head: The first node of linked list.
    @return: True if it has a cycle, or false
    """
    def hasCycle(self, head):
        if not head or not head.next:
            return False
        slow = head
        fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow == fast:
                return True
        return False



class Solution:
    """
    @param head: The first node of linked list.
    @return: True if it has a cycle, or false
    """
    def hasCycle(self, head):
        if not head or not head.next:
            return False
        slow = head
        fast = head
        while fast and fast.next:

            if slow == fast.next or slow==fast.next.next:
                return True
            slow = slow.next
            fast = fast.next.next
        return False


class Solution:
    """
    @param head: The first node of linked list.
    @return: The node where the cycle begins. if there is no cycle, return null
    """
    def detectCycle(self, head):
        # write your code here
        if not head or not head.next:
            return None
        slow, fast=head, head
        while fast and fast.next:
            slow=slow.next
            fast=fast.next.next
            if slow==fast:
                break
        if not fast or not fast.next:
            return None
        t=head
        while t!=slow:
            slow=slow.next
            t=t.next
        return t