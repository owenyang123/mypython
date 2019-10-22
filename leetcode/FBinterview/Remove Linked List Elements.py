class Solution:


    def removeElements(self, head, val):
        if not head:
            return None
        l = []
        while (head and head.val == val):
            head = head.next
        temp = head
        if head != None:
            l.append([temp, temp.val])
        else:
            return None

        while (temp.next != None):
            if temp.next.val != val:
                l.append([temp.next, temp.next.val])
            temp = temp.next
        for i in range(len(l) - 1):
            l[i][0].next = l[i + 1][0]
        l[-1][0].next = None

        return head


class Solution1:
    """
    @param head: a ListNode
    @param val: An integer
    @return: a ListNode
    """

    def removeElements(self, head, val):
        # write your code here

        if not head:
            return

        dummy = ListNode(0)
        dummy.next = head

        start = dummy

        while head:
            if head.val == val:
                start.next = head.next
                head = start
            start = head
            head = head.next
        return dummy.next